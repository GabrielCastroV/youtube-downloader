"""Minimal bilingual ES/EN translation system.

Usage::

    t = Translator("es")
    t.get("ui.download")      # → "Descargar"
    t.set_language("en")
    t.get("ui.download")      # → "Download"
"""

from __future__ import annotations

from typing import Literal

Language = Literal["es", "en"]

_STRINGS: dict[Language, dict[str, str]] = {
    "es": {
        # --- Header ---
        "app.title": "YT Downloader",
        # --- URL input ---
        "ui.url_placeholder": "Pega el enlace de YouTube aquí…",
        "ui.paste": "Pegar",
        "ui.autopaste_prompt": "URL de YouTube detectada. ¿Pegar?",
        "ui.autopaste_yes": "Sí, pegar",
        "ui.autopaste_no": "No",
        # --- Fetch / preview ---
        "ui.fetching": "Obteniendo información…",
        "ui.short_badge": "Short",
        "ui.playlist_badge": "Lista",
        "ui.video_count": "{n} vídeos",
        # --- Format chips ---
        "ui.mode.video_audio": "Vídeo + Audio",
        "ui.mode.audio": "Solo audio",
        "ui.mode.video": "Solo vídeo",
        # --- Quality dropdowns ---
        "ui.quality": "Calidad",
        "ui.best": "Mejor",
        "ui.format": "Formato",
        "ui.resolution": "Resolución",
        "ui.codec": "Códec",
        "ui.container": "Contenedor",
        # --- Advanced panel ---
        "ui.advanced": "Opciones avanzadas",
        "ui.output_folder": "Carpeta de salida",
        "ui.filename_template": "Plantilla de nombre",
        "ui.subtitles": "Subtítulos",
        "ui.subtitle_embed": "Embeber en archivo",
        "ui.subtitle_separate": "Archivos .srt separados",
        "ui.subtitle_languages": "Idiomas",
        "ui.auto_generated": "Incluir auto-generados",
        "ui.embed_thumbnail": "Incrustar miniatura",
        "ui.embed_metadata": "Incrustar metadatos",
        "ui.clip_range": "Recortar vídeo",
        "ui.clip_from": "Desde",
        "ui.clip_to": "Hasta",
        "ui.playlist_range": "Rango de lista",
        "ui.playlist_from": "Desde item",
        "ui.playlist_to": "Hasta item",
        # --- Thumbnail prompt ---
        "ui.embed_thumbnail_prompt": "¿Descargar e incrustar miniatura?",
        "ui.yes": "Sí",
        "ui.no": "No",
        # --- Download button ---
        "ui.download": "Descargar",
        "ui.cancel": "Cancelar",
        "ui.retry": "Reintentar",
        # --- Progress ---
        "ui.preparing": "Preparando…",
        "ui.downloading": "Descargando…",
        "ui.processing": "Procesando…",
        "ui.merging": "Uniendo pistas…",
        "ui.done": "Descarga completada",
        # --- Queue ---
        "ui.queue": "Cola",
        "ui.queue_empty": "La cola está vacía",
        "ui.status.queued": "En espera",
        "ui.status.active": "Descargando",
        "ui.status.done": "Completado",
        "ui.status.error": "Error",
        "ui.status.cancelled": "Cancelado",
        # --- History ---
        "ui.history": "Historial",
        "ui.history_empty": "No hay descargas anteriores",
        "ui.open_file": "Abrir archivo",
        "ui.open_folder": "Abrir carpeta",
        "ui.redownload": "Descargar de nuevo",
        "ui.clear_history": "Borrar historial",
        # --- Settings ---
        "ui.settings": "Configuración",
        "ui.theme": "Tema",
        "ui.theme.dark": "Oscuro",
        "ui.theme.light": "Claro",
        "ui.language": "Idioma",
        "ui.default_folder": "Carpeta por defecto",
        "ui.open_logs": "Abrir carpeta de logs",
        "ui.ffmpeg_section": "FFmpeg",
        "ui.ffmpeg_found": "FFmpeg detectado ✓",
        "ui.ffmpeg_missing_label": "FFmpeg no encontrado",
        "ui.ffmpeg_install_btn": "Instalar FFmpeg",
        "ui.ffmpeg_installing": "Instalando FFmpeg…",
        "ui.about": "Acerca de",
        "ui.concurrent_downloads": "Descargas simultáneas",
        "ui.auto_open": "Abrir archivo al terminar",
        "ui.notify_complete": "Notificar al completar",
        "ui.speed_limit": "Límite de velocidad (KB/s, 0=sin límite)",
        "ui.max_retries": "Reintentos máximos",
        "ui.made_by": "Hecho por",
        # --- Errors ---
        "error.invalid_url": "URL no válida. Asegúrate de pegar un enlace de YouTube.",
        "error.video_unavailable": "El vídeo no está disponible (privado, eliminado o bloqueado).",
        "error.network": "Sin conexión. Comprueba tu internet e inténtalo de nuevo.",
        "error.ffmpeg_missing": "FFmpeg no encontrado. Ve a Configuración para instalarlo.",
        "error.ffmpeg_install": "No se pudo instalar FFmpeg. Inténtalo manualmente.",
        "error.quality_unavailable": "La calidad seleccionada no está disponible para este vídeo.",
        "error.disk_space": "Espacio en disco insuficiente.",
        "error.permission": "Sin permisos para escribir en la carpeta de destino.",
        "error.unexpected": "Error inesperado. Consulta los logs para más detalles.",
        "status.cancelled": "Descarga cancelada.",
        # --- Toasts ---
        "toast.download_done": "¡Descarga completada!",
        "toast.ffmpeg_installed": "FFmpeg instalado correctamente.",
        "toast.history_cleared": "Historial borrado.",
    },
    "en": {
        # --- Header ---
        "app.title": "YT Downloader",
        # --- URL input ---
        "ui.url_placeholder": "Paste a YouTube link here…",
        "ui.paste": "Paste",
        "ui.autopaste_prompt": "YouTube URL detected. Paste it?",
        "ui.autopaste_yes": "Yes, paste",
        "ui.autopaste_no": "No",
        # --- Fetch / preview ---
        "ui.fetching": "Fetching info…",
        "ui.short_badge": "Short",
        "ui.playlist_badge": "Playlist",
        "ui.video_count": "{n} videos",
        # --- Format chips ---
        "ui.mode.video_audio": "Video + Audio",
        "ui.mode.audio": "Audio only",
        "ui.mode.video": "Video only",
        # --- Quality dropdowns ---
        "ui.quality": "Quality",
        "ui.best": "Best",
        "ui.format": "Format",
        "ui.resolution": "Resolution",
        "ui.codec": "Codec",
        "ui.container": "Container",
        # --- Advanced panel ---
        "ui.advanced": "Advanced options",
        "ui.output_folder": "Output folder",
        "ui.filename_template": "Filename template",
        "ui.subtitles": "Subtitles",
        "ui.subtitle_embed": "Embed in file",
        "ui.subtitle_separate": "Separate .srt files",
        "ui.subtitle_languages": "Languages",
        "ui.auto_generated": "Include auto-generated",
        "ui.embed_thumbnail": "Embed thumbnail",
        "ui.embed_metadata": "Embed metadata",
        "ui.clip_range": "Clip video",
        "ui.clip_from": "From",
        "ui.clip_to": "To",
        "ui.playlist_range": "Playlist range",
        "ui.playlist_from": "From item",
        "ui.playlist_to": "To item",
        # --- Thumbnail prompt ---
        "ui.embed_thumbnail_prompt": "Download and embed thumbnail?",
        "ui.yes": "Yes",
        "ui.no": "No",
        # --- Download button ---
        "ui.download": "Download",
        "ui.cancel": "Cancel",
        "ui.retry": "Retry",
        # --- Progress ---
        "ui.preparing": "Preparing…",
        "ui.downloading": "Downloading…",
        "ui.processing": "Processing…",
        "ui.merging": "Merging tracks…",
        "ui.done": "Download complete",
        # --- Queue ---
        "ui.queue": "Queue",
        "ui.queue_empty": "Queue is empty",
        "ui.status.queued": "Queued",
        "ui.status.active": "Downloading",
        "ui.status.done": "Done",
        "ui.status.error": "Error",
        "ui.status.cancelled": "Cancelled",
        # --- History ---
        "ui.history": "History",
        "ui.history_empty": "No previous downloads",
        "ui.open_file": "Open file",
        "ui.open_folder": "Open folder",
        "ui.redownload": "Download again",
        "ui.clear_history": "Clear history",
        # --- Settings ---
        "ui.settings": "Settings",
        "ui.theme": "Theme",
        "ui.theme.dark": "Dark",
        "ui.theme.light": "Light",
        "ui.language": "Language",
        "ui.default_folder": "Default folder",
        "ui.open_logs": "Open log folder",
        "ui.ffmpeg_section": "FFmpeg",
        "ui.ffmpeg_found": "FFmpeg detected ✓",
        "ui.ffmpeg_missing_label": "FFmpeg not found",
        "ui.ffmpeg_install_btn": "Install FFmpeg",
        "ui.ffmpeg_installing": "Installing FFmpeg…",
        "ui.about": "About",
        "ui.concurrent_downloads": "Concurrent downloads",
        "ui.auto_open": "Auto-open file after download",
        "ui.notify_complete": "Notify on complete",
        "ui.speed_limit": "Speed limit (KB/s, 0=unlimited)",
        "ui.max_retries": "Max retries",
        "ui.made_by": "Made by",
        # --- Errors ---
        "error.invalid_url": "Invalid URL. Make sure you paste a YouTube link.",
        "error.video_unavailable": "Video is unavailable (private, removed, or geo-blocked).",
        "error.network": "No connection. Check your internet and try again.",
        "error.ffmpeg_missing": "FFmpeg not found. Go to Settings to install it.",
        "error.ffmpeg_install": "Failed to install FFmpeg. Please install it manually.",
        "error.quality_unavailable": "Selected quality is not available for this video.",
        "error.disk_space": "Not enough disk space.",
        "error.permission": "No permission to write to the output folder.",
        "error.unexpected": "Unexpected error. Check the logs for details.",
        "status.cancelled": "Download cancelled.",
        # --- Toasts ---
        "toast.download_done": "Download complete!",
        "toast.ffmpeg_installed": "FFmpeg installed successfully.",
        "toast.history_cleared": "History cleared.",
    },
}


class Translator:
    """Thread-safe translator.  Language can be changed at runtime."""

    def __init__(self, language: Language = "es") -> None:
        self._language: Language = language

    @property
    def language(self) -> Language:
        return self._language

    def set_language(self, language: Language) -> None:
        self._language = language

    def get(self, key: str, **kwargs: str | int) -> str:
        lang = self._language
        value = _STRINGS.get(lang, {}).get(key) or _STRINGS["en"].get(key) or key
        if kwargs:
            for k, v in kwargs.items():
                value = value.replace(f"{{{k}}}", str(v))
        return value

    # Shortcut so callers can do  t("ui.download")
    def __call__(self, key: str, **kwargs: str | int) -> str:
        return self.get(key, **kwargs)
