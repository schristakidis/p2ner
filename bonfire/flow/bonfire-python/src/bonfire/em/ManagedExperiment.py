class ManagedExperiment(object):
	log_url = experiment_id = None
	
	def __init__(self, id, name, description, status, log_url, experiment_url, xml, em, *args, **kw):
		super(ManagedExperiment, self).__init__(*args, **kw)
		self.id = id
		self.name = name
		self.description = description
		self.status = status
		self.log_url = log_url
		self.experiment_url = experiment_url
		self.xml = xml
		self._em = em
		
	@property
	def url(self):
		return self.id
	