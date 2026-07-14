import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Calibration(): JSX.Element {
  return (
    <PagePlaceholder
      title="Calibration Wizard"
      description="Step-by-step runner for camera intrinsics, servo homing, and pitch-line alignment."
      bullets={[
        'Camera intrinsics calibration',
        'Servo range & homing sequence',
        'Pitch-line reference alignment',
        'Save calibration profile',
      ]}
    />
  );
}
