"use client";

import { KeyboardEvent, useRef, useState } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";

const ACTIONS = [
  { id: "bold", label: "Bold", shortcut: "Control+B" },
  { id: "italic", label: "Italic", shortcut: "Control+I" },
  { id: "heading", label: "Heading" },
  { id: "list", label: "List" },
  { id: "quote", label: "Quote" },
] as const;

export function Editor({
  content,
  onChange,
}: {
  content: string;
  onChange: (html: string, text: string) => void;
}) {
  const [status, setStatus] = useState("No formatting applied.");
  const buttonRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const editor = useEditor({
    extensions: [StarterKit, Placeholder.configure({ placeholder: "Revise a paragraph here. The checker will not rewrite the whole assignment for you." })],
    content,
    immediatelyRender: false,
    editorProps: {
      attributes: {
        class: "min-h-[240px] rounded-md border border-[var(--rule)] bg-white p-4 leading-7 focus:outline-none",
        role: "textbox",
        "aria-multiline": "true",
        "aria-label": "Assignment draft",
        "aria-describedby": "editor-help",
      },
    },
    onUpdate: ({ editor: instance }) => onChange(instance.getHTML(), instance.getText()),
  });

  function announce(label: string, on: boolean) {
    setStatus(`${label} ${on ? "on" : "off"}.`);
  }

  function run(id: (typeof ACTIONS)[number]["id"]) {
    if (!editor) return;
    if (id === "bold") {
      editor.chain().focus().toggleBold().run();
      announce("Bold", editor.isActive("bold"));
    } else if (id === "italic") {
      editor.chain().focus().toggleItalic().run();
      announce("Italic", editor.isActive("italic"));
    } else if (id === "heading") {
      editor.chain().focus().toggleHeading({ level: 2 }).run();
      announce("Heading", editor.isActive("heading", { level: 2 }));
    } else if (id === "list") {
      editor.chain().focus().toggleBulletList().run();
      announce("List", editor.isActive("bulletList"));
    } else {
      editor.chain().focus().toggleBlockquote().run();
      announce("Quote", editor.isActive("blockquote"));
    }
  }

  function onToolbarKey(event: KeyboardEvent<HTMLDivElement>) {
    const current = buttonRefs.current.findIndex((node) => node === document.activeElement);
    if (current < 0) return;
    if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
      event.preventDefault();
      const next = event.key === "ArrowRight"
        ? (current + 1) % ACTIONS.length
        : (current - 1 + ACTIONS.length) % ACTIONS.length;
      buttonRefs.current[next]?.focus();
    }
  }

  if (!editor) return null;
  return (
    <div>
      <p id="editor-help" className="sr-only">
        Use the formatting toolbar, then type in the assignment draft. Control+B and Control+I toggle bold and italic.
      </p>
      <div className="mb-2 flex flex-wrap gap-2 text-sm" role="toolbar" aria-label="Text formatting" aria-controls="assignment-editor" onKeyDown={onToolbarKey}>
        {ACTIONS.map((action, index) => {
          const pressed =
            action.id === "bold" ? editor.isActive("bold")
            : action.id === "italic" ? editor.isActive("italic")
            : action.id === "heading" ? editor.isActive("heading", { level: 2 })
            : action.id === "list" ? editor.isActive("bulletList")
            : editor.isActive("blockquote");
          return (
            <button type="button"
              key={action.id}
              ref={(node) => {
                buttonRefs.current[index] = node;
              }}
              aria-pressed={pressed}
              aria-keyshortcuts={"shortcut" in action ? action.shortcut : undefined}
              className="ac-hit rounded border border-[var(--rule)] px-3"
              onClick={() => run(action.id)}
            >
              {action.label}
            </button>
          );
        })}
      </div>
      <p className="sr-only" aria-live="polite">{status}</p>
      <div id="assignment-editor">
        <EditorContent editor={editor} aria-label="Assignment editor" />
      </div>
    </div>
  );
}
