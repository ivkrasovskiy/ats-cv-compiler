import { createPortal } from 'react-dom'
import { ConfirmDialog } from './ConfirmDialog'
import type { FilePair } from '../utils/outputUtils'

interface RegenDropdown {
  pair: FilePair
  md: string
  top: number
  left: number
}

interface Props {
  deleteTarget: string | null
  saveAsDialog: { original: string; copy: string } | null
  pendingRowSwitch: { pdf: string | null; md: string | null; mode?: 'editor' | 'md-view' } | null
  discardCancelDialog: boolean
  regenDropdown: RegenDropdown | null
  previewPdf: string | null
  onDelete: (name: string) => void
  onCancelDelete: () => void
  onSaveAsCopy: (original: string, copy: string) => void
  onSaveAsOriginal: (original: string) => void
  onConfirmRowSwitch: () => void
  onCancelRowSwitch: () => void
  onConfirmDiscard: () => void
  onCancelDiscard: () => void
  onRegenAuto: (base: string, md: string) => void
  onRerender: (md: string) => void
  onCloseRegen: () => void
}

export function OutputDialogs({
  deleteTarget,
  saveAsDialog,
  pendingRowSwitch,
  discardCancelDialog,
  regenDropdown,
  onDelete,
  onCancelDelete,
  onSaveAsCopy,
  onSaveAsOriginal,
  onConfirmRowSwitch,
  onCancelRowSwitch,
  onConfirmDiscard,
  onCancelDiscard,
  onRegenAuto,
  onRerender,
  onCloseRegen,
}: Props) {
  return (
    <>
      {deleteTarget && (
        <ConfirmDialog
          title="Delete file?"
          message={`Delete "${deleteTarget}"? This cannot be undone.`}
          confirmLabel="Delete"
          onConfirm={() => onDelete(deleteTarget)}
          onCancel={onCancelDelete}
        />
      )}

      {saveAsDialog && (
        <ConfirmDialog
          title="Save as user-edited copy?"
          message={`Save as "${saveAsDialog.copy}" to prevent overwriting on regeneration, or overwrite the original "${saveAsDialog.original}".`}
          confirmLabel="Save as copy"
          cancelLabel="Overwrite original"
          onConfirm={() => onSaveAsCopy(saveAsDialog.original, saveAsDialog.copy)}
          onCancel={() => onSaveAsOriginal(saveAsDialog.original)}
        />
      )}

      {pendingRowSwitch && (
        <ConfirmDialog
          title="Unsaved changes"
          message="You have unsaved changes. Discard them and switch?"
          confirmLabel="Discard"
          cancelLabel="Keep editing"
          onConfirm={onConfirmRowSwitch}
          onCancel={onCancelRowSwitch}
        />
      )}

      {discardCancelDialog && (
        <ConfirmDialog
          title="Discard changes?"
          message="Your unsaved changes will be lost."
          confirmLabel="Discard"
          cancelLabel="Keep editing"
          onConfirm={onConfirmDiscard}
          onCancel={onCancelDiscard}
        />
      )}

      {regenDropdown && createPortal(
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={onCloseRegen}
          />
          <div
            className="fixed z-50 w-56 rounded border border-slate-600 bg-slate-800 shadow-xl"
            style={{ top: regenDropdown.top, left: regenDropdown.left }}
          >
            <button
              onClick={() => { onRegenAuto(regenDropdown.pair.base, regenDropdown.md); onCloseRegen() }}
              className="block w-full px-3 py-2 text-left hover:bg-slate-700"
            >
              <div className="text-xs font-medium text-slate-200">Generate CV</div>
              <div className="mt-0.5 text-xs text-slate-500">AI pipeline → Gemini → original bullets</div>
            </button>
            <button
              onClick={() => { onRerender(regenDropdown.md); onCloseRegen() }}
              className="block w-full border-t border-slate-700 px-3 py-2 text-left hover:bg-slate-700"
            >
              <div className="text-xs font-medium text-slate-200">Rerender MD → PDF</div>
              <div className="mt-0.5 text-xs text-slate-500">Fast, no AI — converts edited markdown to PDF</div>
            </button>
          </div>
        </>,
        document.body,
      )}
    </>
  )
}
