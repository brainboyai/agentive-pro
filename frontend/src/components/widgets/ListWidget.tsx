// frontend/src/components/widgets/ListWidget.tsx
import { widgetStyles } from './widgetStyles'; // Import from the new shared file

export const ListWidget = ({ data }: { data: any }) => (
  <div style={widgetStyles.container}>
    <h3>{data.title}</h3>
    <ul>
      {data.items.map((item: string, index: number) => <li key={index}>{item}</li>)}
    </ul>
  </div>
);