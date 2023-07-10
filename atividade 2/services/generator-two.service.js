module.exports = {
  name: "generator-two",
  actions: {
    publish(ctx) {
      const {topic, message} = ctx.params;
      ctx.call(`topic-${topic}.publish`, {message, from: this.name});
    },
  },
};
