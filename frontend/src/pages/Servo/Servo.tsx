import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Servo(): JSX.Element {
  return (
    <PagePlaceholder
      title="Servo Control"
      description="Send manual pan/tilt commands, home the rig, and trigger an emergency stop."
      bullets={[
        'Pan / tilt slider controls (0–180°)',
        'Homing routine launcher',
        'Emergency stop button',
        'Current position readback',
      ]}
    />
  );
}
