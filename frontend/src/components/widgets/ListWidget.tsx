// frontend/src/components/widgets/ListWidget.tsx
import { widgetStyles } from './widgetStyles';

// The key change: The component now needs to receive the handleSendMessage function
type ListWidgetProps = {
  data: {
    title: string;
    items: string[];
  };
  onSendMessage: (message: string) => void; // This is the function passed from App.tsx
};

export const ListWidget = ({ data, onSendMessage }: ListWidgetProps) => (
  <div style={widgetStyles.container}>
    <h3>{data.title}</h3>
    {/* We now map each item to a button element */}
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {data.items.map((item: string, index: number) => (
        <button 
          key={index} 
          style={widgetStyles.listItemButton} // Added a new style for the buttons
          onClick={() => onSendMessage(item)} // When clicked, it sends the item's text
        >
          {item}
        </button>
      ))}
    </div>
  </div>
);