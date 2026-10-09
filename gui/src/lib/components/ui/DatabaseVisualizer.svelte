<script lang="ts">
	import { tv } from 'tailwind-variants';
	import { SvelteFlow, Background, Controls } from '@xyflow/svelte';
	import type { DBMetadata } from '#lib/types';
	import { metadataToNodesAndEdges, type DatabaseNodeData } from '#lib';
	import DatabaseNode from './DatabaseNode.svelte';
	import {
		Table2,
		Eye,
		Database,
		Key,
		Link2,
		ShieldCheck,
		CheckCircle,
		Layers
	} from '@lucide/svelte';
	import '@xyflow/svelte/dist/style.css';

	interface Props {
		databaseName: string;
		schemaName: string;
		metadata: DBMetadata;
		class?: string;
		onTableSelect?: (tableName: string) => void;
	}

	let { databaseName, schemaName, metadata, class: className = '', onTableSelect }: Props = $props();

	const containerStyle = tv({
		base: 'w-full h-full border border-white/10 rounded-lg overflow-hidden bg-[#161212]',
		variants: {}
	});

	const nodeTypes = {
		databaseNode: DatabaseNode
	};

	const { nodes: rawNodes, edges: rawEdges } = $derived(
		metadataToNodesAndEdges(metadata, databaseName, schemaName)
	);

	const nodes = $derived(
		rawNodes.map((node) => ({
			...node,
			type: 'databaseNode',
			data: {
				...node.data,
				onSelect: () => {
					if (onTableSelect && node.data.type === 'table') {
						onTableSelect(node.data.name);
					}
				}
			}
		}))
	);

	const edges = $derived(rawEdges);

	const isLoading = $derived(rawNodes.length === 0);
</script>

<div class="flex flex-col gap-4 h-full">
	<div class={containerStyle({ class: 'flex-1' })}>
		{#if isLoading}
			<div class="flex items-center justify-center h-full">
				<div class="flex flex-col items-center gap-3">
					<div class="w-8 h-8 border-2 border-[#7ecdf3] border-t-transparent rounded-full animate-spin"></div>
					<span class="text-sm text-[#bfc8ce]">Loading Tables</span>
				</div>
			</div>
		{:else}
			<SvelteFlow
				{nodes}
				{edges}
				{nodeTypes}
				fitView
				nodesDraggable={true}
				nodesConnectable={false}
				elementsSelectable={true}
				proOptions={{ hideAttribution: true }}
			>
				<Background color="#3f484d" gap={16} />
				<Controls
					class="!bg-[#231f1e] !border !border-white/10 !rounded-lg"
					style="color: #bfc8ce"
				/>
			</SvelteFlow>
		{/if}
	</div>

	<div class="flex items-center justify-center gap-6 py-4 text-xs text-[#bfc8ce]">
		<div class="flex items-center gap-2">
			<Table2 size={14} class="text-white/60" />
			<span>Table</span>
		</div>
		<div class="flex items-center gap-2">
			<Eye size={14} class="text-white/60" />
			<span>View</span>
		</div>
		<div class="flex items-center gap-2">
			<Database size={14} class="text-white/60" />
			<span>Materialized View</span>
		</div>
		<div class="flex items-center gap-2">
			<Key size={14} class="text-white/60" />
			<span>Primary Key</span>
		</div>
		<div class="flex items-center gap-2">
			<Link2 size={14} class="text-white/60" />
			<span>Foreign Key</span>
		</div>
		<div class="flex items-center gap-2">
			<ShieldCheck size={14} class="text-white/60" />
			<span>Unique</span>
		</div>
		<div class="flex items-center gap-2">
			<CheckCircle size={14} class="text-white/60" />
			<span>Check</span>
		</div>
		<div class="flex items-center gap-2">
			<Layers size={14} class="text-white/60" />
			<span>Index</span>
		</div>
	</div>
</div>

<style>
	:global(.svelte-flow__attribution) {
		background: linear-gradient(135deg, rgba(126, 205, 243, 0.1) 0%, rgba(249, 191, 0, 0.05) 100%) !important;
		color: #bfc8ce !important;
		border: 1px solid rgba(126, 205, 243, 0.2) !important;
		border-radius: 0.375rem !important;
		padding: 0.375rem 0.75rem !important;
		font-size: 0.7rem !important;
		font-family: 'Poppins', sans-serif !important;
		backdrop-filter: blur(8px) !important;
		transition: all 0.2s ease !important;
	}

	:global(.svelte-flow__attribution:hover) {
		background: linear-gradient(135deg, rgba(126, 205, 243, 0.15) 0%, rgba(249, 191, 0, 0.1) 100%) !important;
		border-color: rgba(126, 205, 243, 0.3) !important;
	}

	:global(.svelte-flow__attribution a) {
		color: #7ecdf3 !important;
		text-decoration: none !important;
		font-weight: 500 !important;
		transition: color 0.2s ease !important;
	}

	:global(.svelte-flow__attribution a:hover) {
		color: #eae0df !important;
	}

	:global(.svelte-flow__controls) {
		background-color: #231f1e !important;
		border: 1px solid rgba(255, 255, 255, 0.1) !important;
		border-radius: 0.5rem !important;
	}

	:global(.svelte-flow__controls-button) {
		background-color: #2d2928 !important;
		border: 1px solid rgba(255, 255, 255, 0.1) !important;
		fill: #bfc8ce !important;
	}

	:global(.svelte-flow__controls-button:hover) {
		background-color: #393433 !important;
		fill: #eae0df !important;
	}

	:global(.svelte-flow__controls-button svg) {
		fill: currentColor !important;
	}
</style>
