// frontend/src/components/Canvas.tsx
import { MapWidget } from './widgets/MapWidget';
import { WeatherWidget } from './widgets/WeatherWidget';
import { ListWidget } from './widgets/ListWidget';

// The key change: The Canvas now needs to receive and pass down the onSendMessage function
type CanvasProps = {
  widgets: any[];
  onSendMessage: (message: string) => void;
};

export const Canvas = ({ widgets, onSendMessage }: CanvasProps) => {
  return (
    <div style={{ padding: '20px', display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
      {widgets.map((widget, index) => {
        switch (widget.widget_type) {
          case 'map':
            return <MapWidget key={index} data={widget} />;
          case 'weather':
            return <WeatherWidget key={index} data={widget} />;
          case 'list':
            // Here, we pass the function down to the ListWidget
            return <ListWidget key={index} data={widget} onSendMessage={onSendMessage} />;
          default:
            return <div key={index}>Unknown widget type</div>;
        }
      })}
    </div>
  );
};