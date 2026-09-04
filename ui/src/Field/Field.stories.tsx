import { Button } from '../Button/Button'
import { Field, Input, Select, Textarea } from './Field'

export default { title: 'Field' }

const frame = { width: 400, padding: 16, display: 'flex', flexDirection: 'column' as const, gap: 14, background: 'var(--bg)' }

export const Form = () => (
  <div style={frame}>
    <Field label="Display name" required>
      <Input defaultValue="Els Vermeulen" />
    </Field>
    <Field label="Work email" hint="Used for sign-in and notifications">
      <Input type="email" placeholder="name@company.be" />
    </Field>
    <Field label="Site">
      <Select defaultValue="gent">
        <option value="gent">Gent</option>
        <option value="antwerpen">Antwerpen</option>
        <option value="brussel">Brussel</option>
      </Select>
    </Field>
    <Field label="Note for the helpdesk">
      <Textarea placeholder="Anything we should know" />
    </Field>
    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
      <Button variant="ghost">Cancel</Button>
      <Button variant="primary">Submit</Button>
    </div>
  </div>
)

export const States = () => (
  <div style={frame}>
    <Field label="Start date" required error="Pick a date in the future">
      <Input type="date" defaultValue="2020-01-01" />
    </Field>
    <Field label="Manager" hint="Read-only, managed by HR">
      <Input defaultValue="Jonas De Smet" disabled />
    </Field>
  </div>
)
