export interface Extension {
	name: string;
	default_version?: string | null;
	installed_version?: string | null;
	comment?: string | null;
}

export interface Column {
	name: string;
	data_type: string;
	is_nullable: string;
	column_default: string;
}

export interface Constraint {
	name: string;
	type: string;
	columns: string[];
	referenced_table?: string | null;
	referenced_columns: string[];
	definition?: string | null;
	is_deferrable?: boolean | null;
	initially_deferred?: boolean | null;
	is_validated?: boolean | null;
	on_update?: string | null;
	on_delete?: string | null;
}

export interface Index {
	name: string;
	indexdef: string;
}

export interface TableMetaData {
	name: string;
	schema_name: string;
	columns: Column[];
	constraints: Constraint[];
	indexes: Index[];
}

export interface ViewColumn {
	column_name: string;
	ordinal_position: number;
	data_type: string;
	is_nullable: string;
}

export interface View {
	name: string;
	schema_name: string;
	owner?: string | null;
	definition?: string | null;
	is_updatable?: boolean | null;
	is_insertable_into?: boolean | null;
	is_trigger_updatable?: boolean | null;
	is_trigger_deletable?: boolean | null;
	is_trigger_insertable_into?: boolean | null;
	is_materialized?: boolean | null;
	description?: string | null;
	columns: ViewColumn[];
}

export interface DBMetadata {
	version: string;
	extensions: Extension[];
	tables: TableMetaData[];
	views: View[];
}
