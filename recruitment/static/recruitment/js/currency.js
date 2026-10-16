document.querySelectorAll('[data-currency="vnd"]').forEach((input) => {
    const formatAmount = () => {
        const original = input.value;
        const digits = original.replace(/,/g, "");
        if (!/^[0-9]*$/.test(digits)) return;

        const digitsToRight = original.slice(input.selectionStart ?? original.length)
            .replace(/,/g, "").length;
        const formatted = digits.replace(/^0+(?=[0-9])/, "")
            .replace(/\B(?=([0-9]{3})+(?![0-9]))/g, ",");
        input.value = formatted;

        if (document.activeElement === input) {
            let position = formatted.length;
            let remaining = digitsToRight;
            while (position > 0 && remaining > 0) {
                position -= 1;
                if (formatted[position] !== ",") remaining -= 1;
            }
            input.setSelectionRange(position, position);
        }
    };

    input.addEventListener("input", formatAmount);
    if (/^(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)$/.test(input.value)) formatAmount();
});
