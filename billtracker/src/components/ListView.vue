<template>
    <div class="m-2">
        <ListView
            class="h-[250px]"
            :columns="columns"
            :rows="rows"
            :options="listOptions"
            row-key="id"
        />
    </div>
</template>
 
<script>
import { ListView, Avatar } from 'frappe-ui';
 
export default {
    components: {
        ListView,
        Avatar
    },
    props: {
        rows: {
            type: Array,
            default: () => []
        },
        columns: {
            type: Array,
            default: () => [
                {
                    label: 'Name',
                    key: 'name',
                    width: 3,
                    getLabel: ({ row }) => row.name,
                },
                {
                    label: 'Email',
                    key: 'email',
                    width: '200px',
                },
                {
                    label: 'Description',
                    key: 'description',
                },
                {
                    label: 'Status',
                    key: 'status',
                },
            ]
        },
        listOptions: {
            type: Object,
            default: () => ({
                selectable: true,
                showTooltip: true,
                resizeColumn: true,
                emptyState: {
                    title: 'No records found',
                    description: 'Create a new record to get started',
                    button: {
                        label: 'New Record',
                        variant: 'solid',
                    },
                },
            })
        }
    }
};
</script>