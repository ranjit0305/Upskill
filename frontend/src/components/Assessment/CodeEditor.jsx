import React from 'react';
import Editor from '@monaco-editor/react';

const CodeEditor = ({
    value,
    onChange,
    language = 'python',
    theme = 'vs-dark',
    height = '400px'
}) => {

    const handleEditorChange = (value) => {
        onChange(value);
    };

    return (
        <div className="code-editor-container" style={{ height, width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
            <Editor
                height="100%"
                language={language}
                theme={theme}
                value={value}
                onChange={handleEditorChange}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 4,
                }}
            />
        </div>
    );
};

export default CodeEditor;
