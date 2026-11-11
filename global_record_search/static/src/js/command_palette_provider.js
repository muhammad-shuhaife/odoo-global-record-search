/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const MIN_CHARS = 3;
const MAX_RESULTS = 40;

const commandCategoryRegistry = registry.category("command_categories");
const commandProviderRegistry = registry.category("command_provider");

commandCategoryRegistry.add(
    "global_record_search",
    { name: _t("Records") },
    { sequence: 5 }
);
commandCategoryRegistry.add(
    "global_record_search_menus",
    { namespace: "/", name: _t("Records") },
    { sequence: 5 }
);

function makeRecordProvider(category) {
    return {
        async provide(options) {
            const term = (options.searchValue || "").trim();
            if (term.length < MIN_CHARS) {
                return [];
            }

            const orm = useService("orm");
            const action = useService("action");
            const commands = [];
            let batch = 0;
            let hasNext = true;

            try {
                while (hasNext && commands.length < MAX_RESULTS) {
                    const result = await orm.silent.call(
                        "global.search",
                        "search_records",
                        [term],
                        { batch }
                    );

                    for (const group of result.groups) {
                        for (const record of group.records) {
                            if (commands.length >= MAX_RESULTS) {
                                break;
                            }
                            commands.push({
                                name: record.subtitle
                                    ? `${group.label}: ${record.name} — ${record.subtitle}`
                                    : `${group.label}: ${record.name}`,
                                category,
                                action: () => action.doAction(
                                    {
                                        type: "ir.actions.act_window",
                                        name: group.label,
                                        res_model: group.model,
                                        res_id: record.id,
                                        views: [[false, "form"]],
                                        target: "current",
                                    },
                                    { clearBreadcrumbs: true }
                                ),
                            });
                        }

                        if (group.has_more && commands.length < MAX_RESULTS) {
                            commands.push({
                                name: _t("See all: %s", group.label),
                                category,
                                action: () => action.doAction(
                                    {
                                        type: "ir.actions.act_window",
                                        name: group.label,
                                        res_model: group.model,
                                        views: [[false, "list"], [false, "form"]],
                                        domain: group.domain,
                                        target: "current",
                                    },
                                    { clearBreadcrumbs: true }
                                ),
                            });
                        }

                        if (commands.length >= MAX_RESULTS) {
                            break;
                        }
                    }

                    hasNext = result.has_next;
                    batch += 1;
                }
            } catch (error) {
                console.warn("Global record search command provider failed", error);
            }

            return commands;
        },
    };
}

commandProviderRegistry.add(
    "global_record_search_default",
    makeRecordProvider("global_record_search")
);
commandProviderRegistry.add(
    "global_record_search_menus",
    { ...makeRecordProvider("global_record_search_menus"), namespace: "/" }
);
