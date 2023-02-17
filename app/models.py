from app import db
from app import app
import redis
import rq
from rq.command import send_stop_job_command
from time import time
import json


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    s_id = db.Column(db.String(64), index=True, unique=True)

    setting_1 = db.Column(db.String(64))

    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    def __repr__(self):
        return '<User {} {}>'.format(self.id, self.s_id)


    def launch_task(self, name, description, *args, **kwargs):
        rq_job = app.task_queue.enqueue('app.run_tasks.' + name, self.id,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        #return Task.query.filter_by(user=self, complete=False).all()
        return Task.query.filter_by(user=self).all()

    def stop_all_tasks(self):
        print("try to kill all tasks")
        #all_t = Task.query.filter_by(user=self, complete=False).all()
        all_t = Task.query.filter_by(user=self).all()
        for t in all_t:
            t.kill_task()
        return

    def delete_all_task(self):
        print("try to delete all tasks")
        #all_t = Task.query.filter_by(user=self, complete=False).all()
        all_t = Task.query.filter_by(user=self).all()
        for t in all_t:
            db.session.delete(t)
        return

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()

        # all_t = Notification.query.filter_by(user_id=self.id).all()
        # for t in all_t:
        #     db.session.delete(t)
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))



class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    s_progress= db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            print('get job error')
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100

    def kill_task(self):
        # send_stop_job_command(app.redis, self.id)
        try:
            send_stop_job_command(app.redis, self.id)
        except:
            job = self.get_rq_job()
            try:
                job.cancel()
            except:
                print('canceled')