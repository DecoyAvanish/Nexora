from locust import HttpUser,between,task
class NexoraUser(HttpUser):
    wait_time=between(.2,1)
    @task(4)
    def health(self):self.client.get("/api/health")
    @task(2)
    def status(self):self.client.get("/api/status")
    @task(1)
    def model_card(self):self.client.get("/api/public/model-card")
