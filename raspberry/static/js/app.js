import { createApp } from 'https://unpkg.com/petite-vue?module';

createApp({
  nivelTambo: 0,
  nivelTinaco: 0,
  isTamboActive: false,
  isTinacoActive: false,
  isBombaActive: false,
  modo: '',
  notificacion: '',

  mqttEvent(type) {
    let mqttEvent;
    if (typeof type !== 'string' && type.target instanceof HTMLInputElement) {
      this.isBombaActive = type.target.checked;
      mqttEvent = new CustomEvent('mqttEvent', {
        detail: type.target.checked ? { type: 'encender' } : { type: 'apagar' },
        bubbles: true,
        composed: true,
      });
      window.dispatchEvent(mqttEvent);
    } else if (typeof type === 'string') {
      this.modo = type;
      mqttEvent = new CustomEvent('mqttEvent', {
        detail: { type },
        bubbles: true,
        composed: true,
      });
      window.dispatchEvent(mqttEvent);
    }
  },
  addListeners() {
    window.addEventListener('niveles', ({ detail } = e) => {
      if (detail.tambo) this.nivelTambo = detail.tambo;
      else if (detail.tinaco) this.nivelTinaco = detail.tinaco;
    });
    window.addEventListener('notificacion', ({ detail } = e) => {
      const { tambo, tinaco, bomba, modo, mensaje } = detail;
      this.isTamboActive = tambo === 'Activado' ? true : false;
      this.isTinacoActive = tinaco === 'Activado' ? true : false;
      this.isBombaActive = bomba === 'Activada' ? true : false;
      this.modo = modo;
      this.notificacion = mensaje;
    });
  },
}).mount();
