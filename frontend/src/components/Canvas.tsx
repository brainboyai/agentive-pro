// frontend/src/components/Canvas.tsx
import { MapWidget } from './widgets/MapWidget';
import { WeatherWidget } from './widgets/WeatherWidget';
import { ListWidget } from './widgets/ListWidget';

// Define a more specific type for our widgets to satisfy ESLint
interface WidgetData {
  widget_type: 'map' | 'weather' | 'list' | string;
  [key: string]: any; // Allow other properties
}

type CanvasProps = {
  widgets: WidgetData[];
};

export const Canvas = ({ widgets }: CanvasProps) => {
  return (
    <div style={{ padding: '20px', display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
      {widgets.map((widget, index) => {
        switch (widget.widget_type) {
          case 'map':
            return <MapWidget key={index} data={widget} />;
          case 'weather':
            return <WeatherWidget key={index} data={widget} />;
          case 'list':
            // --- THE FIX ---
            // The entire 'widget' object from the array is the 'data' for the ListWidget.
            return <ListWidget key={index} data={widget} />;
          default:
            return <div key={index}>Unknown widget type: {widget.widget_type}</div>;
        }
      })}
    </div>
  );
};