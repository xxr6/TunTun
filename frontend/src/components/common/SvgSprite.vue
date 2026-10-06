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
    </defs>
  </svg>
</template>

<script setup lang="ts">
</script>
