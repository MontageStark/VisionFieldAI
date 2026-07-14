import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Streaming(): JSX.Element {
  return (
    <PagePlaceholder
      title="Streaming"
      description="Start, stop, and monitor the streaming pipeline that pushes video to downstream consumers."
      bullets={[
        'Start / stop streaming service',
        'Live FPS & bitrate metrics',
        'RTMP / WebRTC URL display',
        'End-to-end latency readout',
      ]}
    />
  );
}
