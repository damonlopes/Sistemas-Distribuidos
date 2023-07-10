module.exports = {
  name: "generator-one",
  actions: {
    publish(ctx) {
      const {topic, message} = ctx.params;
      ctx.call(`topic-${topic}.publish`, {message, from: this.name});
    },
  },
};
