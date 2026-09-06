"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";

export function Editor({
  content,
  onChange,
}: {
  content: string;
  onChange: (html: string, text: string) => void;
}) {
  const editor = useEditor({
    extensions: [StarterKit, Placeholder.configure({ placeholder: "Revise a paragraph here. The checker will not rewrite the whole assignment for you." })],
    content,
    immediatelyRender: false,
    editorProps: {
      attributes: {
        class: "min-h-[240px] rounded-md border border-[var(--rule)] bg-white p-4 leading-7 focus:outline-none",
      },
    },
    onUpdate: ({ editor: instance }) => onChange(instance.getHTML(), instance.getText()),
  });
  if (!editor) return null;
  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-2 text-sm">
        <button type="button" className="rounded border border-[var(--rule)] px-2 py-1" onClick={() => editor.chain().focus().toggleBold().run()}>Bold</button>
        <button type="button" className="rounded border border-[var(--rule)] px-2 py-1" onClick={() => editor.chain().focus().toggleItalic().run()}>Italic</button>
        <button type="button" className="rounded border border-[var(--rule)] px-2 py-1" onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}>Heading</button>
        <button type="button" className="rounded border border-[var(--rule)] px-2 py-1" onClick={() => editor.chain().focus().toggleBulletList().run()}>List</button>
        <button type="button" className="rounded border border-[var(--rule)] px-2 py-1" onClick={() => editor.chain().focus().toggleBlockquote().run()}>Quote</button>
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
