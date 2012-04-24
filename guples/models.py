from django.db import models
import random
import string

def _generate_random_string(length):
	return "".join(random.choice(string.letters + string.digits) for i in xrange(length))

class Plan(models.Model):
	name       = models.CharField(max_length=512)
	max_guples = models.IntegerField(default = 10)

class GupleStore(models.Model):
	secret_key = models.CharField(max_length=16)
	plan       = models.ForeignKey(Plan)

	def save(self, *args, **kwargs):
		if not self.pk:
			self.secret_key = _generate_random_string(16)

		super(GupleStore, self).save(*args, **kwargs)

class Guple(models.Model):
	guple_store = models.ForeignKey(GupleStore)
	key         = models.TextField(blank=False, null=False)
	value       = models.TextField(blank=True, null=False)