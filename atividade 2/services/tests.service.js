module.exports = {
  name: "tests",
  actions: {
    async flow(ctx) {
      await ctx.call('client-one.subscribe', {topic: 'one'});
      await ctx.call('client-two.subscribe', {topic: 'two'});
      await ctx.call('client-three.subscribe', {topic: 'one'});
      await ctx.call('client-three.subscribe', {topic: 'two'});
      await ctx.call('generator-one.publish', {topic: 'one', message: 'Message 1'});
      await ctx.call('generator-one.publish', {topic: 'two', message: 'Message 2'});
      await ctx.call('generator-two.publish', {topic: 'one', message: 'Message 3'});
      await ctx.call('generator-two.publish', {topic: 'two', message: 'Message 4'});
    },
  },
  created() {
  }
};
