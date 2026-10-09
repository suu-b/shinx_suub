import type { DBMetadata, TableMetaData, View, Constraint } from './types';
import type { Node, Edge } from '@xyflow/svelte';

export interface ColumnData {
	name: string;
	dataType: string;
	isNullable: string;
	isPrimaryKey?: boolean;
	isForeignKey?: boolean;
	isUnique?: boolean;
	isCheck?: boolean;
	checkDefinition?: string;
	referencedTable?: string;
	referencedColumn?: string;
}

export interface IndexData {
	name: string;
	definition: string;
	columns: string[];
	isUnique?: boolean;
}

export interface DatabaseNodeData {
	name: string;
	schemaName: string;
	type: 'table' | 'view' | 'materialized_view';
	columns?: ColumnData[];
	indexes?: IndexData[];
	definition?: string | null;
	[key: string]: unknown;
}

function extractPrimaryKeys(constraints: Constraint[]): Set<string> {
	const primaryKeys = new Set<string>();
	constraints.forEach((constraint) => {
		if (constraint.type === 'p' || constraint.type?.toLowerCase() === 'primary key') {
			constraint.columns.forEach((col) => primaryKeys.add(col));
		}
	});
	return primaryKeys;
}

function extractForeignKeys(constraints: Constraint[]): Map<string, { table: string; column: string }> {
	const foreignKeys = new Map<string, { table: string; column: string }>();
	constraints.forEach((constraint) => {
		if (
			constraint.type === 'f' ||
			constraint.type?.toLowerCase() === 'foreign key'
		) {
			if (constraint.referenced_table && constraint.referenced_columns) {
				constraint.columns.forEach((col, index) => {
					const refCol = constraint.referenced_columns[index];
					if (refCol) {
						foreignKeys.set(col, {
							table: constraint.referenced_table!,
							column: refCol
						});
					}
				});
			}
		}
	});
	return foreignKeys;
}

function extractUniqueConstraints(constraints: Constraint[]): Set<string> {
	const uniqueColumns = new Set<string>();
	constraints.forEach((constraint) => {
		if (constraint.type === 'u' || constraint.type?.toLowerCase() === 'unique') {
			constraint.columns.forEach((col) => uniqueColumns.add(col));
		}
	});
	return uniqueColumns;
}

function extractCheckConstraints(constraints: Constraint[]): Map<string, string> {
	const checkConstraints = new Map<string, string>();
	constraints.forEach((constraint) => {
		if (constraint.type === 'c' || constraint.type?.toLowerCase() === 'check') {
			if (constraint.definition) {
				constraint.columns.forEach((col) => {
					checkConstraints.set(col, constraint.definition!);
				});
			}
		}
	});
	return checkConstraints;
}

function extractIndexes(
	indexes: Array<{ name: string; indexdef: string }>,
	constraints: Constraint[]
): IndexData[] {
	const indexData: IndexData[] = [];
	const uniqueConstraints = extractUniqueConstraints(constraints);

	indexes.forEach((index) => {
		const def = index.indexdef.toLowerCase();
		const isUnique = def.includes('unique');

		const columnsMatch = index.indexdef.match(/\(([^)]+)\)/);
		const columns = columnsMatch
			? columnsMatch[1].split(',').map((c) => c.trim().replace(/"/g, ''))
			: [];

		indexData.push({
			name: index.name,
			definition: index.indexdef,
			columns,
			isUnique
		});
	});

	return indexData;
}

export function metadataToNodesAndEdges(
	metadata: DBMetadata,
	databaseName: string,
	schemaName: string
): { nodes: Node<DatabaseNodeData>[]; edges: Edge[] } {
	const nodes: Node<DatabaseNodeData>[] = [];
	const edges: Edge[] = [];

	const tables = metadata.tables.filter((table) => table.schema_name === schemaName);
	const views = metadata.views.filter((view) => view.schema_name === schemaName);

	const tableNodeMap = new Map<string, string>();

	tables.forEach((table: TableMetaData, index: number) => {
		const primaryKeys = extractPrimaryKeys(table.constraints);
		const foreignKeys = extractForeignKeys(table.constraints);
		const uniqueColumns = extractUniqueConstraints(table.constraints);
		const checkConstraints = extractCheckConstraints(table.constraints);
		const indexes = extractIndexes(table.indexes, table.constraints);

		const nodeId = `table-${databaseName}-${schemaName}-${table.name}`;
		tableNodeMap.set(table.name, nodeId);

		nodes.push({
			id: nodeId,
			type: 'default',
			position: { x: index * 350, y: 0 },
			data: {
				name: table.name,
				schemaName: table.schema_name,
				type: 'table',
				columns: table.columns.map((col) => {
					const fkInfo = foreignKeys.get(col.name);
					return {
						name: col.name,
						dataType: col.data_type,
						isNullable: col.is_nullable,
						isPrimaryKey: primaryKeys.has(col.name),
						isForeignKey: foreignKeys.has(col.name),
						isUnique: uniqueColumns.has(col.name),
						isCheck: checkConstraints.has(col.name),
						checkDefinition: checkConstraints.get(col.name),
						referencedTable: fkInfo?.table,
						referencedColumn: fkInfo?.column
					};
				}),
				indexes
			}
		});
	});

	views.forEach((view: View, index: number) => {
		const viewType = view.is_materialized ? 'materialized_view' : 'view';
		const yPos = view.is_materialized ? 800 : 500;

		nodes.push({
			id: `${viewType}-${databaseName}-${schemaName}-${view.name}`,
			type: 'default',
			position: { x: index * 350, y: yPos },
			data: {
				name: view.name,
				schemaName: view.schema_name,
				type: viewType,
				columns: view.columns.map((col) => ({
					name: col.column_name,
					dataType: col.data_type,
					isNullable: col.is_nullable
				})),
				definition: view.definition
			}
		});
	});

	tables.forEach((table) => {
		const foreignKeys = extractForeignKeys(table.constraints);
		const sourceNodeId = tableNodeMap.get(table.name);

		if (sourceNodeId) {
			foreignKeys.forEach((fkInfo, columnName) => {
				const targetNodeId = tableNodeMap.get(fkInfo.table);
				if (targetNodeId) {
					edges.push({
						id: `edge-${sourceNodeId}-${columnName}-${targetNodeId}-${fkInfo.column}`,
						source: sourceNodeId,
						target: targetNodeId,
						sourceHandle: `${columnName}-right`,
						targetHandle: `${fkInfo.column}-left`,
						type: 'smoothstep',
						style: 'stroke: #bfc8ce; stroke-width: 1.5px;',
						markerEnd: {
							type: 'arrowclosed',
							color: '#bfc8ce'
						}
					});
				}
			});
		}
	});

	return { nodes, edges };
}

