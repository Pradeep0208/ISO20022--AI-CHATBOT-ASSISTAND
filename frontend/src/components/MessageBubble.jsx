export default function MessageBubble({
  text,
  sender,
  isTyping = false,
  darkMode = false,
}) {
  const isUser = sender === "user";

  // Professional Color Scheme
  const userBubbleBg = darkMode ? "#1e40af" : "#2563eb";
  const botBubbleBg = darkMode ? "#1e293b" : "#ffffff";
  const userTextColor = "#ffffff";
  const botTextColor = darkMode ? "#f1f5f9" : "#1e293b";
  const avatarBgUser = darkMode ? "#1e40af" : "#2563eb";
  const avatarBgBot = darkMode ? "#475569" : "#64748b";

  const containerStyle = {
    display: "flex",
    justifyContent: isUser ? "flex-end" : "flex-start",
    marginBottom: 20,
    animation: "fadeIn 0.3s ease-out",
  };

  const rowStyle = {
    display: "flex",
    flexDirection: isUser ? "row-reverse" : "row",
    alignItems: "flex-start",
    gap: 12,
    maxWidth: "75%",
  };

  const avatarStyle = {
    width: 40,
    height: 40,
    borderRadius: "10px",
    background: isUser ? avatarBgUser : avatarBgBot,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
    fontSize: "13px",
    fontWeight: 700,
    letterSpacing: "0.5px",
    boxShadow: darkMode
      ? "0 2px 8px rgba(0, 0, 0, 0.3)"
      : "0 2px 6px rgba(0, 0, 0, 0.12)",
    flexShrink: 0,
  };

  const bubbleStyle = {
    padding: isUser ? "14px 18px" : "16px 20px",
    borderRadius: isUser ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
    backgroundColor: isUser ? userBubbleBg : botBubbleBg,
    color: isUser ? userTextColor : botTextColor,
    maxWidth: "100%",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    boxShadow: darkMode
      ? "0 2px 12px rgba(0, 0, 0, 0.3)"
      : isUser
      ? "0 2px 8px rgba(37, 99, 235, 0.15)"
      : "0 1px 3px rgba(0, 0, 0, 0.1)",
    fontSize: "15px",
    lineHeight: 1.6,
    border: isUser
      ? "none"
      : darkMode
      ? "1px solid #334155"
      : "1px solid #e2e8f0",
    fontWeight: isUser ? 500 : 400,
  };

  const labelStyle = {
    fontSize: "11px",
    fontWeight: 600,
    color: darkMode ? "#94a3b8" : "#64748b",
    marginBottom: 4,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  };

  const typingDotBase = {
    width: 8,
    height: 8,
    borderRadius: "50%",
    backgroundColor: darkMode ? "#94a3b8" : "#64748b",
    display: "inline-block",
  };

  const keyframes = `
    @keyframes typingAnimation {
      0%, 60%, 100% { 
        transform: translateY(0);
        opacity: 0.5;
      }
      30% { 
        transform: translateY(-8px);
        opacity: 1;
      }
    }
  `;

  return (
    <>
      <style>{keyframes}</style>
      <div style={containerStyle}>
        <div style={rowStyle}>
          <div style={avatarStyle}>
            {isUser ? "💭" : "🤖"}
          </div>

          <div>
            {!isUser && (
              <div style={labelStyle}>
                ISO 20022 Assistant
              </div>
            )}
            
            <div style={bubbleStyle}>
              {isTyping ? (
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <span
                    style={{
                      ...typingDotBase,
                      animation: "typingAnimation 1.4s infinite ease-in-out",
                      animationDelay: "0s",
                    }}
                  />
                  <span
                    style={{
                      ...typingDotBase,
                      animation: "typingAnimation 1.4s infinite ease-in-out",
                      animationDelay: "0.2s",
                    }}
                  />
                  <span
                    style={{
                      ...typingDotBase,
                      animation: "typingAnimation 1.4s infinite ease-in-out",
                      animationDelay: "0.4s",
                    }}
                  />
                </div>
              ) : (
                <div
                  style={{
                    fontFamily: isUser
                      ? "inherit"
                      : "'Times New Roman', Times, serif",
                    fontSize: "14px",
                    lineHeight: 1.6,
                  }}
                  dangerouslySetInnerHTML={{
                    __html: formatMessage(text, isUser),
                  }}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// Helper function to format message text with better styling
function formatMessage(text, isUser) {
  if (!text) return "";

  // Don't format user messages - keep them simple
  if (isUser) {
    return escapeHtml(text);
  }

  // Format bot messages with better markdown-like styling
  let formatted = escapeHtml(text);

  // Format bold text with **text**
  formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight: 700; font-size: 14px;">$1</strong>');

  // Format code/XML tags with `text`
  formatted = formatted.replace(/`(.+?)`/g, '<code style="background-color: rgba(100, 116, 139, 0.1); padding: 2px 6px; border-radius: 4px; font-family: \'Monaco\', \'Courier New\', monospace; font-size: 14px;">$1</code>');

  // Format headings (### text) - keep same size as body
  formatted = formatted.replace(/^### (.+)$/gm, '<div style="font-size: 14px; font-weight: 700; margin-top: 16px; margin-bottom: 8px; color: inherit;">$1</div>');

  // Format bullet points with better spacing
  formatted = formatted.replace(/^[•\-\*] (.+)$/gm, '<div style="margin-left: 16px; margin-bottom: 6px; position: relative; padding-left: 8px; font-size: 14px;"><span style="position: absolute; left: -12px;">•</span>$1</div>');

  // Format numbered lists
  formatted = formatted.replace(/^(\d+)\. (.+)$/gm, '<div style="margin-left: 16px; margin-bottom: 6px; font-size: 14px;">$1. $2</div>');

  // Preserve line breaks
  formatted = formatted.replace(/\n/g, '<br />');

  return formatted;
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}