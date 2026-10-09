<template>
  <svg class="svg-sprite" aria-hidden="true" style="position:absolute;width:0;height:0;overflow:hidden">
    <defs>
    <symbol id="i-home" viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V20a1 1 0 0 0 1 1H10v-5.5h4V21h3.5a1 1 0 0 0 1-1V9.5"/></symbol>
    <symbol id="i-cards" viewBox="0 0 24 24"><rect x="3" y="6" width="13" height="15" rx="3"/><path d="M7 3h11a3 3 0 0 1 3 3v11"/><path d="M7 11h5M7 15h7"/></symbol>
    <symbol id="i-folder" viewBox="0 0 24 24"><path d="M3 7.5A2.5 2.5 0 0 1 5.5 5h3.2a2 2 0 0 1 1.6.8l1 1.4H18a2.5 2.5 0 0 1 2.5 2.5v6.8A2.5 2.5 0 0 1 18 19H5.5A2.5 2.5 0 0 1 3 16.5z"/></symbol>
    <symbol id="i-book" viewBox="0 0 24 24"><path d="M4 5.5A2 2 0 0 1 6 3.5h5v16H6a2 2 0 0 0-2 2z"/><path d="M20 5.5a2 2 0 0 0-2-2h-5v16h5a2 2 0 0 1 2 2z"/></symbol>
    <symbol id="i-timer" viewBox="0 0 24 24"><circle cx="12" cy="13.5" r="8"/><path d="M12 9.5v4l2.5 2"/><path d="M9 2.5h6"/></symbol>
    <symbol id="i-chart" viewBox="0 0 24 24"><path d="M3 20h18"/><path d="M6.5 20v-6M12 20V6M17.5 20v-9"/></symbol>
    <symbol id="i-gear" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.2"/><path d="M19.4 14.5a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1v.3a2 2 0 1 1-4 0v-.2a1.6 1.6 0 0 0-2.7-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H3.4a2 2 0 1 1 0-4h.2a1.6 1.6 0 0 0 1.1-2.7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 2.7-1.1V3.4a2 2 0 1 1 4 0v.2a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0 1.1 2.7h.3a2 2 0 1 1 0 4h-.2a1.6 1.6 0 0 0-1.5 1z"/></symbol>
    <symbol id="i-check" viewBox="0 0 24 24"><path d="M4.5 12.5 9.5 17.5 19.5 6.5"/></symbol>
    <symbol id="i-spark" viewBox="0 0 24 24"><path d="M12 3l2 5.5 5.5 2-5.5 2-2 5.5-2-5.5L4.5 10.5 10 8.5z"/><path d="M18.5 16.5l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/></symbol>
    <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></symbol>
    <symbol id="i-close" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></symbol>
    <symbol id="i-play" viewBox="0 0 24 24"><path d="M7 4.5 19 12 7 19.5z" stroke-linejoin="round"/></symbol>
    <symbol id="i-pause" viewBox="0 0 24 24"><path d="M8.5 5v14M15.5 5v14"/></symbol>
    <symbol id="i-upload" viewBox="0 0 24 24"><path d="M12 16V4.5"/><path d="M7.5 9 12 4.5 16.5 9"/><path d="M4 15v3.5A2 2 0 0 0 6 20.5h12a2 2 0 0 0 2-2V15"/></symbol>
    <symbol id="i-flame" viewBox="0 0 24 24"><path d="M12 3s5 4.2 5 9a5 5 0 0 1-10 0c0-1.6.7-3 1.5-4 .2 1.3 1 2.2 2 2.2 1.4 0 2.2-1.2 2.2-2.8 0-1.7-.7-3.2-.7-4.4z"/><path d="M7 13a5 5 0 0 0 10 0"/></symbol>
    <symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/></symbol>
    <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5.2l3.2 2"/></symbol>
    <symbol id="i-brain" viewBox="0 0 24 24"><path d="M9.5 4.5A3 3 0 0 0 6.6 8 3 3 0 0 0 5 10.8a3 3 0 0 0 1.4 2.5A3 3 0 0 0 9.5 19.5h.6V4.5z"/><path d="M14.5 4.5A3 3 0 0 1 17.4 8 3 3 0 0 1 19 10.8a3 3 0 0 1-1.4 2.5 3 3 0 0 1-3.1 6.2h-.6V4.5z"/><path d="M12 4.5v15"/></symbol>
    <symbol id="i-doc" viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/></symbol>
    <symbol id="i-quote" viewBox="0 0 24 24"><path d="M9 6.5C6.5 8 5.5 10 5.5 12.5A3 3 0 1 0 9 15c0-1.3-.6-2.2-1.5-2.6.1-1.4.9-2.5 2.3-3.3z"/><path d="M18 6.5c-2.5 1.5-3.5 3.5-3.5 6A3 3 0 1 0 18 15c0-1.3-.6-2.2-1.5-2.6.1-1.4.9-2.5 2.3-3.3z"/></symbol>
    <symbol id="i-code" viewBox="0 0 24 24"><path d="M8.5 8 4.5 12l4 4"/><path d="M15.5 8l4 4-4 4"/><path d="M13.5 5l-3 14"/></symbol>
    <symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/></symbol>
    <symbol id="i-link" viewBox="0 0 24 24"><path d="M10 13.5a4 4 0 0 0 5.7 0l2.6-2.6a4 4 0 0 0-5.7-5.7L11.5 6.4"/><path d="M14 10.5a4 4 0 0 0-5.7 0L5.7 13a4 4 0 0 0 5.7 5.7l1.1-1.1"/></symbol>
    <symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
    <symbol id="i-refresh" viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v4.5h-4.5"/></symbol>
    <symbol id="i-moon" viewBox="0 0 24 24"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/></symbol>
    <symbol id="i-film" viewBox="0 0 24 24"><rect x="2.5" y="4.5" width="19" height="15" rx="3"/><path d="M7 4.5v15M17 4.5v15"/><path d="M2.5 9.5h4.5M2.5 14.5h4.5M17 9.5h4.5M17 14.5h4.5"/></symbol>
    <symbol id="i-download" viewBox="0 0 24 24"><path d="M12 3.5v11"/><path d="M7.5 10.5 12 15l4.5-4.5"/><path d="M4 18.5v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1"/></symbol>
    <symbol id="i-copy" viewBox="0 0 24 24"><rect x="8.5" y="8.5" width="12" height="12" rx="3"/><path d="M15.5 5.5v-.5a2 2 0 0 0-2-2H5.5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h.5"/></symbol>
    <symbol id="i-scissor" viewBox="0 0 24 24"><circle cx="6.5" cy="6.5" r="2.6"/><circle cx="6.5" cy="17.5" r="2.6"/><path d="M8.7 8.3 20 18.5"/><path d="M8.7 15.7 20 5.5"/><path d="M12 13.5l2 2"/></symbol>
    <symbol id="i-bolt" viewBox="0 0 24 24"><path d="M13.5 2.5 5 13.5h5l-1.5 8L19 10h-5.5z"/></symbol>
    <symbol id="i-star" viewBox="0 0 24 24"><path d="M12 3.5l2.6 5.6 6.1.7-4.5 4.2 1.2 6-5.4-3-5.4 3 1.2-6L3.3 9.8l6.1-.7z"/></symbol>
    <symbol id="i-crown" viewBox="0 0 24 24"><path d="M3.5 18h17"/><path d="M3.5 7.5l4 4 4.5-7 4.5 7 4-4v8h-17z"/></symbol>
    <symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4"/></symbol>
    <symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 3 5 5.8v5.4c0 4.5 3 7.8 7 9.3 4-1.5 7-4.8 7-9.3V5.8z"/><path d="M9 12l2.2 2.2L15.4 10"/></symbol>
    <symbol id="i-calendar" viewBox="0 0 24 24"><rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17"/><path d="M8 3v4M16 3v4"/></symbol>
    <symbol id="i-compass" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="M15.5 8.5l-2 5.5-5.5 2 2-5.5z"/></symbol>
    <symbol id="i-gem" viewBox="0 0 24 24"><path d="M12 3 4 9.5 12 21l8-11.5z"/><path d="M4 9.5h16"/><path d="M9 9.5 12 21l3-11.5"/></symbol>
    <symbol id="i-library" viewBox="0 0 24 24"><path d="M4 4.5h5v15H4zM15 4.5h5v15h-5z"/><path d="M9 7h6M9 17h6"/></symbol>
    <symbol id="i-video-link" viewBox="0 0 24 24"><rect x="2.5" y="5.5" width="13" height="13" rx="3"/><path d="M15.5 10.5l6-3.5v10l-6-3.5"/></symbol>
    <symbol id="i-md" viewBox="0 0 24 24"><rect x="2.5" y="5" width="19" height="14" rx="3"/><path d="M6 15V9l2.5 3L11 9v6"/><path d="M14.5 9v6h2.5a1.8 1.8 0 0 0 1.8-1.8v-2.4A1.8 1.8 0 0 0 17 9z"/></symbol>
    <symbol id="i-palette" viewBox="0 0 24 24"><path d="M12 3.5a8.5 8.5 0 0 0 0 17c1.4 0 2.2-.9 2.2-2 0-.6-.2-1-.6-1.4-.3-.4-.5-.8-.5-1.3 0-1 .8-1.8 1.9-1.8h1.7A4.3 4.3 0 0 0 21 12.7C21 7.7 17 3.5 12 3.5z"/><circle cx="7.6" cy="11.4" r="1.15" fill="currentColor" stroke="none"/><circle cx="11" cy="7.8" r="1.15" fill="currentColor" stroke="none"/><circle cx="15.2" cy="8.6" r="1.15" fill="currentColor" stroke="none"/></symbol>
    <symbol id="i-chev" viewBox="0 0 24 24"><path d="M9.5 5.5 16 12l-6.5 6.5"/></symbol>
    <symbol id="i-tomato" viewBox="0 0 24 24"><circle cx="12" cy="13.8" r="7.2"/><path d="M12 6.6C9.6 5.9 8 6.2 6.4 7.3c1.5.4 2.6 1 3.3 1.9M12 6.6c2.4-.7 4-.4 5.6.7-1.5.4-2.6 1-3.3 1.9"/><path d="M12 6.4c-.3-1.3.2-2.3 1.1-3.1"/></symbol>
    <symbol id="i-leaf" viewBox="0 0 24 24"><path d="M19.5 4.5C11 5 6 10 5.5 18.5 14 18 19 13 19.5 4.5z"/><path d="M6.5 17.5C9.5 13 13 9.5 17 7"/></symbol>
    <symbol id="i-cup" viewBox="0 0 24 24"><path d="M5 9h11v5.5a4.5 4.5 0 0 1-4.5 4.5h-2A4.5 4.5 0 0 1 5 14.5z"/><path d="M16 10h1.4a2.8 2.8 0 0 1 0 5.6h-2"/><path d="M8.5 5.5c0-1 .7-1.2.7-2.2M12 5.5c0-1 .7-1.2.7-2.2"/></symbol>
    <symbol id="i-buddy" viewBox="0 0 24 24"><rect x="3.5" y="3.5" width="17" height="17" rx="5.5"/><circle cx="9.2" cy="10.3" r="1.05" fill="currentColor" stroke="none"/><circle cx="14.8" cy="10.3" r="1.05" fill="currentColor" stroke="none"/><path d="M8.7 14.3c.95 1.05 2.05 1.6 3.3 1.6s2.35-.55 3.3-1.6"/></symbol>
    <symbol id="i-pen" viewBox="0 0 24 24"><path d="M4.5 19.5l.7-4L16.6 4.1a2 2 0 0 1 2.8 0l.5.5a2 2 0 0 1 0 2.8L8.5 18.8z"/><path d="M14.8 6l3.2 3.2"/></symbol>
    <symbol id="i-cam" viewBox="0 0 24 24"><path d="M4 8.5A2.5 2.5 0 0 1 6.5 6h1.2l1.2-1.8h6.2L16.3 6h1.2A2.5 2.5 0 0 1 20 8.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 16.5z"/><circle cx="12" cy="12.3" r="3.4"/></symbol>
    <symbol id="i-exit" viewBox="0 0 24 24"><path d="M14 4.5H7A2.5 2.5 0 0 0 4.5 7v10A2.5 2.5 0 0 0 7 19.5h7"/><path d="M10.5 12H20"/><path d="M16.5 8.5 20 12l-3.5 3.5"/></symbol>
    <symbol id="i-back" viewBox="0 0 24 24"><path d="M19 12H5"/><path d="M11 6 5 12l6 6"/></symbol>
    <symbol id="i-dots" viewBox="0 0 24 24"><circle cx="5.5" cy="12" r="1.15" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.15" fill="currentColor" stroke="none"/><circle cx="18.5" cy="12" r="1.15" fill="currentColor" stroke="none"/></symbol>
    <symbol id="i-cloud" viewBox="0 0 24 24"><path d="M7 18.5a4.5 4.5 0 0 1-.4-9A5.5 5.5 0 0 1 17.3 8.7 4 4 0 0 1 17 18.5z"/><path d="M12 15.5v-5"/><path d="M9.8 12.5 12 10.3l2.2 2.2"/></symbol>
    <symbol id="i-list" viewBox="0 0 24 24"><path d="M9 6.5h11M9 12h11M9 17.5h11"/><circle cx="4.8" cy="6.5" r="1.1" fill="currentColor" stroke="none"/><circle cx="4.8" cy="12" r="1.1" fill="currentColor" stroke="none"/><circle cx="4.8" cy="17.5" r="1.1" fill="currentColor" stroke="none"/></symbol>
    <symbol id="i-expand" viewBox="0 0 24 24"><path d="M9 3.5H5A1.5 1.5 0 0 0 3.5 5v4"/><path d="M15 3.5h4A1.5 1.5 0 0 1 20.5 5v4"/><path d="M9 20.5H5A1.5 1.5 0 0 1 3.5 19v-4"/><path d="M15 20.5h4a1.5 1.5 0 0 0 1.5-1.5v-4"/></symbol>
    <symbol id="i-zoom-out" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M8 11h6"/><path d="M16 16l4 4"/></symbol>
    <symbol id="i-zoom-in" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M8 11h6M11 8v6"/><path d="M16 16l4 4"/></symbol>
    <symbol id="i-coll" viewBox="0 0 24 24"><path d="M9 3.5H5A1.5 1.5 0 0 0 3.5 5v4"/><path d="M15 3.5h4A1.5 1.5 0 0 1 20.5 5v4"/><path d="M3.5 15v4A1.5 1.5 0 0 0 5 20.5h4"/><path d="M20.5 15v4a1.5 1.5 0 0 1-1.5 1.5h-4"/></symbol>
    <!-- ── 专注页番茄吉祥物：红色外套、奶油脸、绿叶，与品牌形象呼应 ── -->
    <symbol id="m-tomato" viewBox="0 0 64 64">
      <path d="M31 13c-.4-3.5 1.2-6.2 4.4-8" fill="none" stroke="#347642" stroke-width="3" stroke-linecap="round"/>
      <path d="M31 18c-5.1-2.7-11.1-2.2-14.8 1.3 3.8.4 6.5 2.5 8.6 5.1z" fill="#4c9949" stroke="#3a241d" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M31 18c5.1-2.7 11.1-2.2 14.8 1.3-3.8.4-6.5 2.5-8.6 5.1z" fill="#4c9949" stroke="#3a241d" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M32 15c-2.3 2-3.6 5.1-3.7 8.1h7.4c-.1-3-1.4-6.1-3.7-8.1z" fill="#347642" stroke="#3a241d" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M12.5 39c0-13.2 8.2-20.5 19.5-20.5S51.5 25.8 51.5 39c0 9.8-7.6 16.5-19.5 16.5S12.5 48.8 12.5 39z" fill="#f34b38" stroke="#3a241d" stroke-width="3"/>
      <path d="M18.8 33.4c2.2-7.5 6.8-10.8 11.2-11.4" fill="none" stroke="#ff8f79" stroke-width="3" stroke-linecap="round" opacity=".85"/>
      <path d="M19 40.6c0-8.1 5-13.4 13-13.4s13 5.3 13 13.4c0 7.6-5.4 12.8-13 12.8S19 48.2 19 40.6z" fill="#fff4e7" stroke="#3a241d" stroke-width="2.6"/>
      <ellipse cx="27.3" cy="39" rx="2" ry="3.2" fill="#3a241d"/>
      <ellipse cx="36.7" cy="39" rx="2" ry="3.2" fill="#3a241d"/>
      <ellipse cx="23.4" cy="45" rx="3" ry="1.8" fill="#f8a39d"/>
      <ellipse cx="40.6" cy="45" rx="3" ry="1.8" fill="#f8a39d"/>
      <path d="M28.8 45.4c2.1 2.6 4.3 2.6 6.4 0" fill="none" stroke="#3a241d" stroke-width="2.3" stroke-linecap="round"/>
      <path d="M16.3 48.5c-3.2.8-4.7 4.8-2.5 6.6 2.4 1.9 5.1-.3 6-2" fill="#fff4e7" stroke="#3a241d" stroke-width="2.4" stroke-linecap="round"/>
      <path d="M47.7 48.5c3.2.8 4.7 4.8 2.5 6.6-2.4 1.9-5.1-.3-6-2" fill="#fff4e7" stroke="#3a241d" stroke-width="2.4" stroke-linecap="round"/>
    </symbol>
    <symbol id="m-tomato-read" viewBox="0 0 64 64">
      <use href="#m-tomato" />
      <rect x="23" y="44" width="20" height="13" rx="2.5" fill="#fffaf2" stroke="#3a241d" stroke-width="2.3"/>
      <path d="M27 48.5h11M27 52h8" fill="none" stroke="#9c9694" stroke-width="1.8" stroke-linecap="round"/>
    </symbol>
    <symbol id="m-sprout" viewBox="0 0 64 64">
      <path d="M32 56V33" fill="none" stroke="var(--mint-d)" stroke-width="3.6" stroke-linecap="round"/>
      <path d="M31.5 38c.3-8.5-4.8-13.6-14.6-14.4.6 9.2 5.6 14.2 14.6 14.4z" fill="var(--mint)" stroke="var(--line)" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M32.5 34c-.3-7.4 4.4-11.8 13-12.6-.5 8-4.8 12.4-13 12.6z" fill="var(--mint)" stroke="var(--line)" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M22 56.5c1.5-4.4 5.4-6.8 10-6.8s8.5 2.4 10 6.8z" fill="var(--warm)" stroke="var(--line)" stroke-width="2.4" stroke-linejoin="round"/>
    </symbol>
    </defs>
  </svg>
</template>

<script setup lang="ts">
</script>
