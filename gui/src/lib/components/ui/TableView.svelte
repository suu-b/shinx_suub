<script lang="ts">
	import type { TableMetaData, Column, Constraint } from '#lib/types';
	import { Key, Link2, ShieldCheck, CheckCircle } from '@lucide/svelte';

	interface Props {
		table: TableMetaData;
	}

	let { table }: Props = $props();

	// Extract constraints
	const primaryKeys = $derived.by(() => {
		const keys = new Set<string>();
		table.constraints.forEach((constraint: Constraint) => {
			if (constraint.type === 'p' || constraint.type?.toLowerCase() === 'primary key') {
				constraint.columns.forEach((col: string) => keys.add(col));
			}
		});
		return keys;
	});

	const foreignKeys = $derived.by(() => {
		const keys = new Set<string>();
		table.constraints.forEach((constraint: Constraint) => {
			if (constraint.type === 'f' || constraint.type?.toLowerCase() === 'foreign key') {
				constraint.columns.forEach((col: string) => keys.add(col));
			}
		});
		return keys;
	});

	const uniqueColumns = $derived.by(() => {
		const cols = new Set<string>();
		table.constraints.forEach((constraint: Constraint) => {
			if (constraint.type === 'u' || constraint.type?.toLowerCase() === 'unique') {
				constraint.columns.forEach((col: string) => cols.add(col));
			}
		});
		return cols;
	});

	const checkConstraints = $derived.by(() => {
		const checks = new Map<string, string>();
		table.constraints.forEach((constraint: Constraint) => {
			if (constraint.type === 'c' || constraint.type?.toLowerCase() === 'check') {
				if (constraint.definition) {
					constraint.columns.forEach((col: string) => {
						checks.set(col, constraint.definition!);
					});
				}
			}
		});
		return checks;
	});

	// Mock data - will be replaced with real data later
	const mockData: Record<string, string | number>[] = [
		{ id: 1, email: 'user1@example.com', name: 'John Doe', age: 25, created_at: '2024-01-15 10:30:00' },
		{ id: 2, email: 'user2@example.com', name: 'Jane Smith', age: 30, created_at: '2024-01-16 14:20:00' },
		{ id: 3, email: 'user3@example.com', name: 'Bob Johnson', age: 28, created_at: '2024-01-17 09:15:00' }
	];
</script>

<div class="flex flex-col h-full">
	<div class="flex items-center gap-2 mb-4">
		<h2 class="text-sm font-bold text-[#eae0df]">{table.name}</h2>
		<span class="text-xs text-[#bfc8ce]">{table.schema_name}</span>
	</div>

	<div class="flex-1 overflow-auto border border-white/10 rounded-lg bg-[#231f1e]">
		<table class="w-full text-xs border-collapse">
			<thead class="sticky top-0 bg-[#2d2928]">
				<tr>
					{#each table.columns as column}
						<th class="px-3 py-2 text-left font-medium text-[#bfc8ce] border-b border-r border-white/10">
							<div class="flex items-center gap-1">
								<div class="flex items-center gap-0.5">
									{#if primaryKeys.has(column.name)}
										<Key size={10} class="text-white/50" />
									{/if}
									{#if foreignKeys.has(column.name)}
										<Link2 size={10} class="text-white/50" />
									{/if}
									{#if uniqueColumns.has(column.name)}
										<ShieldCheck size={10} class="text-white/50" />
									{/if}
									{#if checkConstraints.has(column.name)}
										<CheckCircle size={10} class="text-white/50" />
									{/if}
								</div>
								<span>{column.name}</span>
							</div>
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each mockData as row}
					<tr class="border-b border-white/5 hover:bg-white/5 transition-colors">
						{#each table.columns as column}
							<td class="px-3 py-2 text-[#eae0df] border-r border-white/5">
								{row[column.name as keyof typeof row] || null}
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
