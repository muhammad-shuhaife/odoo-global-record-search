/** @odoo-module **/

import { CommandPalette } from "@web/core/commands/command_palette";
import "@web/core/dialog/dialog";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";

const CLOSE_FALLBACK_MS = 240;

function playCloseAnimation() {
    const palette = document.querySelector(".o_command_palette");
    if (!palette || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return Promise.resolve();
    }

    palette.classList.add("o_grs_closing");
    return new Promise((resolve) => {
        let timeout;
        const finish = () => {
            clearTimeout(timeout);
            palette.removeEventListener("animationend", onAnimationEnd);
            resolve();
        };
        const onAnimationEnd = (event) => {
            if (event.target === palette && event.animationName === "grs-palette-exit") {
                finish();
            }
        };
        palette.addEventListener("animationend", onAnimationEnd);
        timeout = setTimeout(finish, CLOSE_FALLBACK_MS);
    });
}

const dialogService = registry.category("services").get("dialog");
patch(dialogService, {
    start(...args) {
        const dialog = super.start(...args);
        const addDialog = dialog.add.bind(dialog);

        dialog.add = (Component, props, options = {}) => {
            if (Component !== CommandPalette) {
                return addDialog(Component, props, options);
            }

            const onClose = options.onClose;
            return addDialog(Component, props, {
                ...options,
                async onClose(...closeArgs) {
                    await playCloseAnimation();
                    return onClose?.(...closeArgs);
                },
            });
        };

        return dialog;
    },
});
