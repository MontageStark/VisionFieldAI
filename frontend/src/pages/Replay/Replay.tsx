import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Replay(): JSX.Element {
  return (
    <PagePlaceholder
      title="Replay Viewer"
      description="Browse, scrub, and export previously captured replays stored in the replay_data directory."
      bullets={[
        'Timeline scrubber with keyframe previews',
        'Track overlays (players, ball)',
        'Bookmarks & clip export',
        'Camera-perspective switcher',
      ]}
    />
  );
}
