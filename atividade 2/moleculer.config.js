module.exports = {
  namespace: '',
  nodeID: null,

  metadata: {},
  logger: true,

  transporter: 'NATS',

  requestTimeout: 30000, // 30s

  maxCallLevel: 100,
  heartbeatInterval: 10,
  heartbeatTimeout: 30,

  registry: {
    strategy: 'RoundRobin',
    preferLocal: true
  },

  validator: {type: 'Fastest'},

  created(broker) {
  },

  started(broker) {
  },

  stopped(broker) {
  }
};
