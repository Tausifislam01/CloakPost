// static/js/chat.js
(function (global) {
  const listeners = {};
  function on(event, handler) {
    (listeners[event] ||= []).push(handler);
    return () => {
      const arr = listeners[event];
      const i = arr.indexOf(handler);
      if (i >= 0) arr.splice(i, 1);
    };
  }
  function emit(event, payload) {
    (listeners[event] || []).forEach(h => {
      try { h(payload); } catch (e) { console.error(e); }
    });
  }

  function connect(threadId) {
    let sock;
    let closed = false;
    let tries = 0;

    const scheme = (window.location.protocol === "https:") ? "wss" : "ws";
    const url = `${scheme}://${window.location.host}/ws/threads/${threadId}/`;

    function open() {
      if (closed) return;
      sock = new WebSocket(url);

      sock.onopen = () => { tries = 0; emit("open"); };
      sock.onclose = () => {
        emit("close");
        if (!closed) retry();
      };
      sock.onerror = (e) => { console.error("ws error", e); };
      sock.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          // Normalize Channels JsonWebsocketConsumer messages
          const event = data.event || data.type;
          if (event) emit(event, data);
          // Also surface common events
          if (event === "message_new") emit("message_new", data.message);
          if (event === "message_seen") emit("message_seen", { message_id: data.message_id });
          if (event === "message_deleted") emit("message_deleted", { message_id: data.message_id });
        } catch (err) {
          console.error("bad ws payload", err);
        }
      };
    }

    function retry() {
      tries += 1;
      const delay = Math.min(30000, 500 * Math.pow(2, tries)); // exp backoff
      setTimeout(open, delay);
    }

    function send(payload) {
      const data = JSON.stringify(payload);
      if (sock && sock.readyState === 1) {
        sock.send(data);
      } else {
        // queue-one-shot: try to send after next open
        const off = on("open", () => { off(); try { sock.send(data); } catch(e){} });
      }
    }

    open();

    return {
      send, 
      close() { closed = true; try { sock && sock.close(); } catch(e){}; },
    };
  }

  global.Chat = { connect, on };
})(window);