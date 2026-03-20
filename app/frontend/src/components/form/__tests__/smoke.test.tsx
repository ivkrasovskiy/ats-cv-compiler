// Smoke imports — verify all form primitives export without errors
import { FieldRow } from '../FieldRow'
import { MonthInput } from '../MonthInput'
import { LinkList } from '../LinkList'

test('FieldRow exports', () => { expect(FieldRow).toBeDefined() })
test('MonthInput exports', () => { expect(MonthInput).toBeDefined() })
test('LinkList exports', () => { expect(LinkList).toBeDefined() })
