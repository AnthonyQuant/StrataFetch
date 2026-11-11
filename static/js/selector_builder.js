document.addEventListener('DOMContentLoaded', () => {
    const loadUrlBtn = document.getElementById('load-url-btn');
    const targetUrlInput = document.getElementById('target-url-input');
    const pageFrame = document.getElementById('page-frame');
    const statusBar = document.getElementById('status-bar');
    const fieldRuleForm = document.getElementById('field-rule-form');
    const cssSelectorInput = document.getElementById('css-selector');
    const rulesList = document.getElementById('rules-list');

    let activeRules = [];

    loadUrlBtn.addEventListener('click', async () => {
        const url = targetUrlInput.value.trim();
        if (!url) {
            alert('Please enter a valid URL.');
            return;
        }

        statusBar.innerText = `Fetching ${url}...`;

        try {
            const response = await fetch('/api/selector/proxy-fetch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            if (!response.ok) throw new Error('Proxy fetch failed');

            const html = await response.text();
            const doc = pageFrame.contentWindow.document;
            doc.open();
            doc.write(html);
            doc.close();

            statusBar.innerText = 'Page loaded. Hover and click elements inside the frame to capture selectors.';
            attachFrameClickListeners();

        } catch (err) {
            statusBar.innerText = `Error: ${err.message}`;
        }
    });

    function attachFrameClickListeners() {
        const doc = pageFrame.contentWindow.document;

        doc.addEventListener('mouseover', (e) => {
            e.target.style.outline = '2px solid #8b5cf6';
        });

        doc.addEventListener('mouseout', (e) => {
            e.target.style.outline = '';
        });

        doc.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const target = e.target;
            const selector = generateSimpleSelector(target);
            cssSelectorInput.value = selector;
            statusBar.innerText = `Captured selector: ${selector}`;
        });
    }

    function generateSimpleSelector(el) {
        if (el.id) return `#${el.id}`;
        if (el.className && typeof el.className === 'string') {
            const classes = el.className.trim().split(/\s+/).join('.');
            if (classes) return `${el.tagName.toLowerCase()}.${classes}`;
        }
        return el.tagName.toLowerCase();
    }

    fieldRuleForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const fieldName = document.getElementById('field-name').value.trim();
        const selector = cssSelectorInput.value.trim();
        const dataType = document.getElementById('data-type').value;

        if (!fieldName || !selector) return;

        const rule = { fieldName, selector, dataType };
        activeRules.push(rule);
        renderRulesList();

        document.getElementById('field-name').value = '';
        cssSelectorInput.value = '';
    });

    function renderRulesList() {
        rulesList.innerHTML = '';
        activeRules.forEach((rule, index) => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${rule.fieldName}</strong>: <code>${rule.selector}</code> (${rule.dataType})`;
            rulesList.appendChild(li);
        });
    }
});