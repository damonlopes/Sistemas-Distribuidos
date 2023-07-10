module.exports = {
  name: "client-one",
  actions: {
    subscribe(ctx) {
      ctx.call(`topic-${ctx.params.topic}.subscribe`, {clientName: this.name});
    },
    receiveMessage(ctx) {
      console.log(`${this.name} received message: `, ctx.params);
    }
  },
};
