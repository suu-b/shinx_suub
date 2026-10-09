import re

import psycopg

from shinx.db import DatabaseAdapter

from shinx.shared.models.db_metadata import (
    Column,
    Constraint,
    DBMetadata,
    Extension,
    Index,
    TableMetaData,
    View,
    ViewColumn,
)

from shinx.shared.models.plan_node import PlanNode


class PostgresAdapter(DatabaseAdapter):

    def __init__(self, host, port, dbname, user, password):

        super().__init__()

        self._connection = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )

    def close(self) -> None:

        if self._connection:
            try:
                self._connection.close()
            finally:
                self._connection = None

    def get_database_structure(self) -> DBMetadata:

        self._ensure_connected()

        database_info = self._get_database_info()
        tables = self._get_tables()
        views = self._get_views()

        return DBMetadata(
            version=database_info["version"],
            extensions=[Extension(**item) for item in database_info["extensions"]],
            tables=tables,
            views=views,
        )

    def explain(self, query) -> PlanNode:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        with conn.cursor() as cur:
            cur.execute(f"EXPLAIN (FORMAT JSON) {query}")
            result = cur.fetchone()

        if result is None:
            raise RuntimeError("PostgreSQL returned no execution plan")

        raw_plan = result[0]

        return PlanNode.from_postgres(raw_plan[0]["Plan"])

    def _ensure_connected(self):

        if not self._connection:
            raise RuntimeError("Not connected to a PostgreSQL database")

    @staticmethod
    def _extract_version(version_output: str) -> str:

        match = re.search(r"PostgreSQL\s+(\d+(?:\.\d+)?)", version_output)

        if match:
            return match.group(1)

        return version_output.strip()

    def _get_search_path(self) -> str:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        with conn.cursor() as cur:
            cur.execute("SHOW search_path;")
            row = cur.fetchone()

            if row is None:
                return ""

            return row[0]

    def _get_database_info(self) -> dict:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version_row = cur.fetchone()

            if version_row is None:
                raise RuntimeError("Could not fetch PostgreSQL version")

            version = self._extract_version(version_row[0])

            cur.execute(
                """
                SELECT name, default_version, installed_version, comment
                FROM pg_available_extensions;
                """
            )

            extensions = [
                {
                    "name": row[0],
                    "default_version": row[1],
                    "installed_version": row[2],
                    "comment": row[3],
                }
                for row in cur.fetchall()
            ]

        return {"version": version, "extensions": extensions}

    def _get_tables(self) -> list[TableMetaData]:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        query = """
        SELECT
            table_schema,
            table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema NOT IN ('pg_catalog', 'information_schema', 'msar')
        ORDER BY table_schema, table_name;
        """

        with conn.cursor() as cur:
            cur.execute(query)

            return [
                TableMetaData(
                    name=t,
                    schema_name=s,
                    columns=self._get_columns(s, t),
                    constraints=self._get_constraints(s, t),
                    indexes=self._get_indexes(s, t),
                )
                for s, t in cur.fetchall()
            ]

    def get_tables(self) -> list[TableMetaData]:

        return self._get_tables()

    def _get_columns(self, schema, table) -> list[Column]:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position;
        """

        with conn.cursor() as cur:
            cur.execute(query, (schema, table))

            return [
                Column(
                    name=row[0],
                    data_type=row[1],
                    is_nullable=row[2],
                    column_default=row[3] or "",
                )
                for row in cur.fetchall()
            ]

    def _get_constraints(self, schema, table) -> list[Constraint]:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        query = """
            SELECT
                con.conname AS constraint_name,

                CASE con.contype
                    WHEN 'p' THEN 'PRIMARY KEY'
                    WHEN 'u' THEN 'UNIQUE'
                    WHEN 'f' THEN 'FOREIGN KEY'
                    WHEN 'c' THEN 'CHECK'
                    WHEN 'x' THEN 'EXCLUSION'
                    ELSE con.contype::text
                END AS constraint_type,

                ARRAY(
                    SELECT a.attname
                    FROM unnest(con.conkey)
                         WITH ORDINALITY AS k(attnum, ord)
                    JOIN pg_catalog.pg_attribute a
                      ON a.attrelid = con.conrelid
                     AND a.attnum = k.attnum
                    ORDER BY k.ord
                ) AS columns,

                CASE
                    WHEN con.contype = 'f'
                    THEN rn.nspname || '.' || rc.relname
                    ELSE NULL
                END AS referenced_table,

                CASE
                    WHEN con.contype = 'f'
                    THEN ARRAY(
                        SELECT a.attname
                        FROM unnest(con.confkey)
                             WITH ORDINALITY AS k(attnum, ord)
                        JOIN pg_catalog.pg_attribute a
                          ON a.attrelid = con.confrelid
                         AND a.attnum = k.attnum
                        ORDER BY k.ord
                    )
                    ELSE NULL
                END AS referenced_columns,

                pg_catalog.pg_get_constraintdef(con.oid, true)
                    AS definition,

                con.condeferrable AS is_deferrable,
                con.condeferred AS initially_deferred,
                con.convalidated AS is_validated,

                CASE con.confupdtype
                    WHEN 'a' THEN 'NO ACTION'
                    WHEN 'r' THEN 'RESTRICT'
                    WHEN 'c' THEN 'CASCADE'
                    WHEN 'n' THEN 'SET NULL'
                    WHEN 'd' THEN 'SET DEFAULT'
                    ELSE NULL
                END AS on_update,

                CASE con.confdeltype
                    WHEN 'a' THEN 'NO ACTION'
                    WHEN 'r' THEN 'RESTRICT'
                    WHEN 'c' THEN 'CASCADE'
                    WHEN 'n' THEN 'SET NULL'
                    WHEN 'd' THEN 'SET DEFAULT'
                    ELSE NULL
                END AS on_delete

            FROM pg_catalog.pg_constraint con

            JOIN pg_catalog.pg_class tbl
              ON tbl.oid = con.conrelid

            JOIN pg_catalog.pg_namespace ns
              ON ns.oid = tbl.relnamespace

            LEFT JOIN pg_catalog.pg_class rc
              ON rc.oid = con.confrelid

            LEFT JOIN pg_catalog.pg_namespace rn
              ON rn.oid = rc.relnamespace

            WHERE ns.nspname = %s
              AND tbl.relname = %s

            ORDER BY con.conname;
        """

        with conn.cursor() as cur:
            cur.execute(query, (schema, table))

            constraints = []

            for row in cur.fetchall():
                (
                    name,
                    constraint_type,
                    columns,
                    referenced_table,
                    referenced_columns,
                    definition,
                    is_deferrable,
                    initially_deferred,
                    is_validated,
                    on_update,
                    on_delete,
                ) = row

                constraint = Constraint(
                    name=name,
                    type=constraint_type,
                    columns=list(columns or []),
                    referenced_table=referenced_table,
                    referenced_columns=list(referenced_columns or []),
                    definition=definition,
                    is_deferrable=is_deferrable,
                    initially_deferred=initially_deferred,
                    is_validated=is_validated,
                    on_update=on_update,
                    on_delete=on_delete,
                )

                if referenced_table is not None:
                    constraint.referenced_table = referenced_table
                    constraint.referenced_columns = list(
                        referenced_columns or []
                    )

                constraints.append(constraint)

        return constraints

    def get_constraints(self, schema, table):

        return self._get_constraints(schema, table)

    def _get_indexes(self, schema, table) -> list[Index]:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        query = """
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = %s
              AND tablename = %s;
        """

        with conn.cursor() as cur:
            cur.execute(query, (schema, table))

            return [
                Index(name=row[0], indexdef=row[1])
                for row in cur.fetchall()
            ]

    def get_indexes(self, schema, table):

        return self._get_indexes(schema, table)

    def _get_views(self) -> list[View]:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        view_query = """
        SELECT
            schemaname,
            viewname,
            viewowner,
            definition
        FROM pg_catalog.pg_views
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, viewname;
        """

        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'information_schema'
                  AND table_name = 'views';
            """)

            available_view_columns = {row[0] for row in cur.fetchall()}

            view_info_fields = [
                "table_schema",
                "table_name",
                "is_updatable",
                "is_insertable_into",
                "is_trigger_updatable",
                "is_trigger_deletable",
                "is_trigger_insertable",
            ]

            selected_view_info_fields = [
                field
                for field in view_info_fields
                if field in available_view_columns
            ]

            view_info_query = f"""
            SELECT
                {', '.join(selected_view_info_fields)}
            FROM information_schema.views
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema');
            """

            view_columns_query = """
            SELECT
                table_schema,
                table_name,
                column_name,
                ordinal_position,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name, ordinal_position;
            """

            matview_query = """
            SELECT
                schemaname,
                matviewname,
                matviewowner,
                definition,
                tablespace
            FROM pg_catalog.pg_matviews
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, matviewname;
            """

            description_query = """
            SELECT
                n.nspname AS schema_name,
                c.relname AS view_name,
                obj_description(c.oid, 'pg_class') AS description
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n
                ON n.oid = c.relnamespace
            WHERE c.relkind = 'v'
              AND n.nspname NOT IN ('pg_catalog', 'information_schema');
            """

            cur.execute(view_query)

            pg_views = {
                (schema_name, view_name): {
                    "owner": owner,
                    "definition": definition,
                }
                for schema_name, view_name, owner, definition in cur.fetchall()
            }

            if selected_view_info_fields:
                cur.execute(view_info_query)

                info_map = {}

                for row in cur.fetchall():
                    row_data = dict(zip(selected_view_info_fields, row))

                    key = (
                        row_data["table_schema"],
                        row_data["table_name"],
                    )

                    info_map[key] = {
                        "is_updatable": row_data.get("is_updatable"),
                        "is_insertable_into": row_data.get("is_insertable_into"),
                        "is_trigger_updatable": row_data.get("is_trigger_updatable"),
                        "is_trigger_deletable": row_data.get("is_trigger_deletable"),
                        "is_trigger_insertable": row_data.get("is_trigger_insertable"),
                    }
            else:
                info_map = {}

            cur.execute(view_columns_query)

            columns_map: dict[tuple[str, str], list[ViewColumn]] = {}

            for (
                schema_name,
                view_name,
                column_name,
                ordinal_position,
                data_type,
                is_nullable,
            ) in cur.fetchall():

                key = (schema_name, view_name)

                columns_map.setdefault(key, []).append(
                    ViewColumn(
                        column_name=column_name,
                        ordinal_position=ordinal_position,
                        data_type=data_type,
                        is_nullable=is_nullable,
                    )
                )

            cur.execute(matview_query)

            matviews = {
                (schema_name, matview_name): {
                    "owner": owner,
                    "definition": definition,
                    "tablespace": tablespace,
                }
                for (
                    schema_name,
                    matview_name,
                    owner,
                    definition,
                    tablespace,
                ) in cur.fetchall()
            }

            cur.execute(description_query)

            descriptions = {
                (schema_name, view_name): description
                for schema_name, view_name, description in cur.fetchall()
            }

        view_names = (
            set(pg_views)
            | set(info_map)
            | set(columns_map)
            | set(descriptions)
            | set(matviews)
        )

        views: list[View] = []

        for schema_name, view_name in sorted(view_names):
            key = (schema_name, view_name)

            pg_view = pg_views.get(key, {})
            info = info_map.get(key, {})
            desc = descriptions.get(key)
            view_columns = columns_map.get(key, [])
            matview = matviews.get(key)

            owner = pg_view.get("owner")
            definition = pg_view.get("definition")

            if not owner and matview:
                owner = matview.get("owner")

            if not definition and matview:
                definition = matview.get("definition")

            view = View(
                name=view_name,
                schema_name=schema_name,
                owner=owner,
                definition=definition,
                is_updatable=info.get("is_updatable"),
                is_insertable_into=info.get("is_insertable_into"),
                is_trigger_updatable=info.get("is_trigger_updatable"),
                is_trigger_deletable=info.get("is_trigger_deletable"),
                is_trigger_insertable=info.get("is_trigger_insertable"),
                is_materialized=matview is not None,
                description=desc,
                columns=view_columns,
            )

            views.append(view)

        return views

    def get_views(self):

        return self._get_views()

    def get_database_info(self) -> dict:

        return self._get_database_info()

    def list_table_names(self, schema_name: str = "public") -> list[str]:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema = %s
            ORDER BY table_name;
        """

        with conn.cursor() as cur:
            cur.execute(query, (schema_name,))

            return [row[0] for row in cur.fetchall()]

    def get_table_metadata(
        self,
        table_name: str,
        schema_name: str = "public",
    ) -> TableMetaData | None:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        query = """
            SELECT 1
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema = %s
              AND table_name = %s;
        """

        with conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))

            if cur.fetchone() is None:
                return None

        return TableMetaData(
            name=table_name,
            schema_name=schema_name,
            columns=self._get_columns(schema_name, table_name),
            constraints=self._get_constraints(schema_name, table_name),
            indexes=self._get_indexes(schema_name, table_name),
        )

    def get_table_stats(self, table_name: str, schema_name: str = "public") -> dict:

        self._ensure_connected()

        conn = self._connection

        if conn is None:
            raise RuntimeError("Not connected to a PostgreSQL database")

        query = """
            SELECT
                c.reltuples::bigint AS estimated_rows,
                pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
                COALESCE(s.n_live_tup, 0) AS live_tuples,
                COALESCE(s.n_dead_tup, 0) AS dead_tuples
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
            WHERE n.nspname = %s AND c.relname = %s;
        """

        with conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))

            row = cur.fetchone()

            if not row:
                return {
                    "table_name": table_name,
                    "schema_name": schema_name,
                    "error": (
                        f"Table '{table_name}' in schema "
                        f"'{schema_name}' was not found."
                    ),
                }

            estimated_rows = max(0, int(row[0])) if row[0] is not None else 0
            live_tuples = int(row[2]) if row[2] is not None else 0
            disk_size = row[1] or "0 bytes"

            row_count = live_tuples if live_tuples > 0 else estimated_rows

            if row_count == 0:
                try:
                    cur.execute(
                        'SELECT count(*) FROM '
                        f'"{schema_name}"."{table_name}";'
                    )

                    cnt = cur.fetchone()

                    if cnt:
                        row_count = cnt[0]

                except Exception:
                    pass

            return {
                "table_name": table_name,
                "schema_name": schema_name,
                "row_count": row_count,
                "disk_size": disk_size,
                "dead_tuples": row[3],
            }