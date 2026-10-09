<script lang="ts">
	import { tv } from 'tailwind-variants';
	import { Handle, Position } from '@xyflow/svelte';
	import {
		Table2,
		Eye,
		Database,
		Table,
		Key,
		Link2,
		ShieldCheck,
		CheckCircle,
		Layers,
		Info
	} from '@lucide/svelte';

	interface IndexData {
		name: string;
		definition: string;
		columns: string[];
		isUnique?: boolean;
	}

	interface ColumnData {
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

	interface DatabaseNodeData {
		name: string;
		schemaName: string;
		type: 'table' | 'view' | 'materialized_view';
		columns?: ColumnData[];
		indexes?: IndexData[];
		definition?: string | null;
		onSelect?: () => void;
		[key: string]: unknown;
	}

	interface Props {
		data: DatabaseNodeData;
	}

	let { data }: Props = $props();

	const nodeStyle = tv({
		base: 'p-4 rounded-lg border min-w-[280px] text-on-surface transition-all duration-200',
		variants: {
			type: {
				table: 'bg-[#231f1e] border border-white/10',
				view: 'bg-[#2d2928] border border-dashed border-white/20',
				materialized_view: 'bg-[#393433] border border-[#f9bf00]/30'
			}
		},
		defaultVariants: {
			type: 'table'
		}
	});

	const iconColorMap = {
		table: 'text-[#7ecdf3]',
		view: 'text-[#899298]',
		materialized_view: 'text-[#f9bf00]'
	};

	const iconColor = $derived(iconColorMap[data.type]);
</script>

<div
	class={nodeStyle({ type: data.type })}
	style="box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.2);"
>
	<div class="flex items-center gap-2 mb-3">
		{#if data.type === 'table'}
			<Table2 size={18} class={iconColor} />
		{:else if data.type === 'view'}
			<Eye size={18} class={iconColor} />
		{:else if data.type === 'materialized_view'}
			<Database size={18} class={iconColor} />
		{/if}
		<h3 class="font-bold text-lg">{data.name}</h3>
		<button
			class="ml-auto p-1 rounded hover:bg-white/10 transition-colors text-[#899298] hover:text-[#bfc8ce]"
			title="Table info"
			onclick={() => data.onSelect?.()}
		>
			<Info size={16} />
		</button>
		{#if data.type === 'materialized_view'}
			<span
				class="px-2 py-0.5 text-xs font-medium rounded bg-[#f9bf00]/20 text-[#f9bf00] border border-[#f9bf00]/30"
			>
				MATVIEW
			</span>
		{/if}
	</div>
	<div class="text-xs text-[#bfc8ce] mb-3">
		{data.schemaName} • {data.type.replace('_', ' ')}
	</div>
	{#if data.columns && data.columns.length > 0}
		<div class="space-y-0">
			{#each data.columns as column, index}
				<div
					class="flex flex-col group relative {index < data.columns.length - 1 && !column.checkDefinition ? 'border-b border-white/5' : ''}"
				>
					<div class="flex items-center justify-between text-sm py-2">
						<div class="flex items-center gap-2 flex-1">
							{#if column.isPrimaryKey}
								<Key size={12} class="text-[#7ecdf3]" />
							{:else if column.isForeignKey}
								<Link2 size={12} class="text-[#f9bf00]" />
							{:else if column.isUnique}
								<ShieldCheck size={12} class="text-[#899298]" />
							{:else if column.isCheck}
								<CheckCircle size={12} class="text-[#bfc8ce]" />
							{:else}
								<span class="w-3"></span>
							{/if}
							<span class="font-medium {column.isPrimaryKey ? 'text-[#7ecdf3]' : ''}">{column.name}</span>
						</div>
						<span class="text-[#bfc8ce] text-xs">{column.dataType}</span>

						{#if column.isForeignKey || column.isPrimaryKey}
							<Handle
								id={column.isForeignKey ? `${column.name}-right` : `${column.name}-left`}
								type={column.isForeignKey ? 'source' : 'target'}
								position={Position.Right}
								class="!bg-[#f9bf00] !w-2 !h-2 !border-0 !opacity-0 group-hover:!opacity-100"
							/>
						{/if}
					</div>
					{#if column.checkDefinition}
						<div class="text-xs text-[#bfc8ce] italic pl-5 pb-2 border-b border-white/5">
							CHECK: {column.checkDefinition}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
	{#if data.indexes && data.indexes.length > 0}
		<div class="mt-3 pt-3 border-t border-white/10">
			<div class="flex items-center gap-1 text-xs text-[#bfc8ce] mb-2">
				<Layers size={12} />
				<span class="font-medium">Indexes</span>
			</div>
			<div class="space-y-1">
				{#each data.indexes as index}
					<div class="flex items-center gap-2 text-xs">
						{#if index.isUnique}
							<ShieldCheck size={10} class="text-[#899298]" />
						{:else}
							<Table size={10} class="text-[#bfc8ce]" />
						{/if}
						<span class="text-[#bfc8ce]">{index.name}</span>
						<span class="text-[#899298]">({index.columns.join(', ')})</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
	{#if data.definition}
		<div class="mt-3 pt-3 border-t border-white/10">
			<p class="text-xs text-[#bfc8ce] italic">{data.definition.slice(0, 100)}...</p>
		</div>
	{/if}
</div>
