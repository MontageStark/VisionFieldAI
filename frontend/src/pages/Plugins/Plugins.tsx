import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Plugins(): JSX.Element {
  return (
    <PagePlaceholder
      title="Plugin Marketplace"
      description="Install and manage reusable Director plugins (analytics, framing presets, overlays, etc.)."
      bullets={[
        'Browse & search plugins',
        'One-click install / uninstall',
        'Per-plugin configuration panel',
        'Version & provenance info',
      ]}
    />
  );
}
