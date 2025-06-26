// frontend/src/components/Canvas.tsx
import { MapWidget } from './widgets/MapWidget';
import { WeatherWidget } from './widgets/WeatherWidget';
import { ListWidget } from './widgets/ListWidget';

export const Canvas = ({ widgets }: { widgets: any[] }) => {
  return (
    <div style={{ padding: '20px', display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
      {widgets.map((widget, index) => {
        switch (widget.widget_type) {
          case 'map':
            return <MapWidget key={index} data={widget} />;
          case 'weather':
            return <WeatherWidget key={index} data={widget} />;
          case 'list':
            return <ListWidget key={index} data={widget} />;
          default:
            return <div key={index}>Unknown widget type</div>;
        }
      })}
    </div>
  );
};