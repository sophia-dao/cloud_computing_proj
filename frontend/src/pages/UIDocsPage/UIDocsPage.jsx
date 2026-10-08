
import { useState } from "react";

import Button from "../../components/common/Button/Button";
import { docsRegistry } from "./docsRegistry";

import "./UIDocsPage.css";

function UIDocsPage() {
    const [selectedId, setSelectedId] = useState(
        docsRegistry[0].id
    );
    const [copied, setCopied] = useState(false);

    const selectedDoc =
        docsRegistry.find((doc) => doc.id === selectedId) ??
        docsRegistry[0];

    const Preview = selectedDoc.Preview;

    async function handleCopy() {
        try {
            await navigator.clipboard.writeText(selectedDoc.code);
            setCopied(true);
        } catch {
            setCopied(false);
        }
    }

    function selectComponent(id) {
        setSelectedId(id);
        setCopied(false);
    }

    return (
        <div className="ui-docs">

            <div className="ui-docs__layout">
                <aside className="ui-docs__sidebar">
                    <h2>Components</h2>

                    <nav aria-label="UI components">
                        {docsRegistry.map((doc) => (
                            <button
                                key={doc.id}
                                type="button"
                                className={
                                    "ui-docs__nav-item" +
                                    (selectedId === doc.id
                                        ? " ui-docs__nav-item--active"
                                        : "")
                                }
                                aria-current={
                                    selectedId === doc.id ? "true" : undefined
                                }
                                onClick={() => selectComponent(doc.id)}
                            >
                                {doc.name}
                            </button>
                        ))}
                    </nav>
                </aside>

                <main className="ui-docs__content">
                    <header className="ui-docs__page-header">
                        <h1>UI Documentation</h1>
                        <p>
                            Explore reusable components, preview their behavior,
                            and copy usage examples.
                        </p>
                    </header>
                    <div className="ui-docs__component-header">
                        <h2>{selectedDoc.name}</h2>
                        <p>{selectedDoc.description}</p>
                    </div>

                    <section className="ui-docs__section">
                        <h3>Live Preview</h3>

                        <div className="ui-docs__preview">
                            <Preview />
                        </div>
                    </section>

                    <section className="ui-docs__section">
                        <h3>File Location</h3>
                        <code className="ui-docs__file-path">
                            {selectedDoc.file}
                        </code>
                    </section>

                    <section className="ui-docs__section">
                        <h3>Props Reference</h3>

                        <div className="ui-docs__table-wrapper">
                            <table className="ui-docs__table">
                                <thead>
                                    <tr>
                                        <th>Prop</th>
                                        <th>Type</th>
                                        <th>Default</th>
                                        <th>Description</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {selectedDoc.props.map((prop) => (
                                        <tr key={prop[0]}>
                                            {prop.map((value, index) => (
                                                <td key={index}>{value}</td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    <section className="ui-docs__section">
                        <div className="ui-docs__section-heading">
                            <h3>Usage Example</h3>

                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={handleCopy}
                            >
                                {copied ? "Copied!" : "Copy Code"}
                            </Button>
                        </div>

                        <pre className="ui-docs__code">
                            <code>{selectedDoc.code}</code>
                        </pre>
                    </section>
                </main>
            </div>
        </div>
    );
}

export default UIDocsPage;
