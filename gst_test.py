import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# GStreamer initialisieren
Gst.init(None)

# Testpipeline: Farbquelle → Anzeige
pipeline = Gst.parse_launch("videotestsrc ! autovideosink")

print("✅ Starte GStreamer-Testpipeline… (Beende mit STRG+C)")

# Pipeline starten
pipeline.set_state(Gst.State.PLAYING)

# Nachricht abwarten: Ende oder Fehler
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

# Auswertung
if msg.type == Gst.MessageType.EOS:
    print("✅ GStreamer-Test erfolgreich beendet (EOS empfangen).")
elif msg.type == Gst.MessageType.ERROR:
    err, dbg = msg.parse_error()
    print(f"❌ GStreamer-Fehler: {err.message}")
else:
    print("⚠️ Unbekannte Nachricht empfangen.")

# Aufräumen
pipeline.set_state(Gst.State.NULL)
print("🚫 Pipeline gestoppt.")
