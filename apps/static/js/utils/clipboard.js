// Simple helper with UIkit notification fallback
export async function copyToClipboard(text) {
  try {
    if (!navigator.clipboard) throw new Error("Clipboard API unsupported");
    await navigator.clipboard.writeText(text);
    if (window.UIkit?.notification) {
      UIkit.notification({ message: "Copied!", status: "success", timeout: 1200 });
    } else {
      alert(`You have copied: ${text}`);
    }
  } catch (err) {
    console.error("Copy failed:", err);
    if (window.UIkit?.notification) {
      UIkit.notification({ message: "Copy failed", status: "danger", timeout: 1500 });
    } else {
      alert("Something went wrong with copy.");
    }
  }
}