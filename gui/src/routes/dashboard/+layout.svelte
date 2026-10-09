<script lang="ts">
	import type { LayoutProps } from './$types';
	import Picker from '#lib/components/primitives/Picker.svelte';
	import { Search, Copy } from "@lucide/svelte";

	let { children }: LayoutProps = $props();

	let selectedSchema = $state("public");
	let searchQuery = $state("");

	const handleSchemaSelect = (value: string) => {
		selectedSchema = value;
	};

	const databaseSchema = [
		{
			name: "public",
			tables: ["users", "orders", "products", "categories"]
		},
		{
			name: "analytics",
			tables: ["events", "metrics", "reports"]
		},
		{
			name: "auth",
			tables: ["sessions", "permissions", "roles"]
		}
	];
</script>

<div class="flex flex-col h-full">
    <div class="p-4 flex items-center gap-2">
        <div class="flex items-center">
            <span class="text-xs font-semibold text-on-surface-variant tracking-wider">SCHEMA</span>
            <Picker label="Schema" value={selectedSchema} onSelect={handleSchemaSelect} class="mx-2 mr-3">
                {#each databaseSchema as schema}
                    <button
                        type="button"
                        class="px-3 py-1.5 text-sm text-on-surface hover:bg-white/10 cursor-pointer w-full text-left transition-colors"
                        onclick={() => handleSchemaSelect(schema.name)}
                        role="menuitem"
                    >{schema.name}</button>
                {/each}
            </Picker>
        </div>
        <div class="flex-1 max-w-md">
            <div class="relative">
                <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                    type="text"
                    placeholder="Search table"
                    bind:value={searchQuery}
                    class="w-full pl-10 pr-4 py-1.5 rounded-md bg-white/5 border border-white/10 text-sm text-on-surface placeholder:text-white/40 focus:outline-none focus:border-white/20 focus:bg-white/10 transition-all"
                />
            </div>
        </div>
        <div class="ml-auto flex items-center gap-2">
            <span class="text-sm text-on-surface-variant">Copy as JSON</span>
            <button
                class="p-1.5 rounded-md bg-transparent text-on-surface border border-white/20 hover:border-white/30 hover:bg-white/5 transition-all cursor-pointer"
            >
                <Copy size={14} />
            </button>
        </div>
    </div>
    <div class="flex-1 overflow-auto">
        {@render children()}
    </div>
</div>
