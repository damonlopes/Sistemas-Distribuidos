module.exports = {
  name: "topic-two",
  actions: {
    subscribe(ctx) {
      this.subscribers.push(ctx.params.clientName);
    },
    publish(ctx) {
      const {message, from} = ctx.params;
      this.subscribers.forEach(clientName => {
        ctx.call(clientName + '.receiveMessage', {message, from, through: this.name});
      })
    }
  },
  created() {
    this.subscribers = [];
  }
};
