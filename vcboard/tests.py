from django.test import TestCase
from vcboard.models import Forum, Thread, Post

def authorize(case, username):
    case.client.login(username, 'password')

class ForumTester(TestCase):
    fixtures = ('vcboard',)

    def setUp(self):
        self.ann = Forum.objects.get(pk=2)

    def testForumPaths(self):
        # tests the forum path functionality
        self.assertEquals('main-forum-category/announcements',
                          self.ann.path)
        helpful = Forum.objects.create(name='Helpful Hints', parent=self.ann)
        self.assertEquals('main-forum-category/announcements/helpful-hints',
                          helpful.path)

    def testSlugCreation(self):
        # makes sure that unique slugs are always created
        helpful = Forum.objects.create(name='Helpful Hints', parent=self.ann)
        self.assertEquals('helpful-hints', helpful.slug)
        helpful2 = Forum.objects.create(name='Helpful Hints', parent=self.ann)
        self.assertEquals('helpful-hints_', helpful2.slug)

    def testWithPath(self):
        # ensures that a forum can always be located by its path
        match = Forum.objects.with_path('main-forum-category/announcements')
        self.assertEquals(self.ann.id, match.id)

        helpful = Forum.objects.get(pk=3)
        match = Forum.objects.with_path('main-forum-category/helpful-hints')
        self.assertEquals(helpful.id, match.id)

class ThreadTester(TestCase):
    fixtures = ('vcboard',)
    urls = 'vcboard.urls'

    def setUp(self):
        self.ann = Forum.objects.get(pk=2)

    def testPostThread(self):
        # makes sure a user can create new threads when appropriate
        count = Thread.objects.count()
        data = {
            'subject': 'This is a test',
            'content': 'This is a test'
        }
        response = self.client.post('/main-forum-category/announcements/new/', data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Thread.objects.count(), 0)
        self.fail()

    def testCloseThread(self):
        # makes sure that users cannot reply to closed threads
        self.fail()

    def testMoveThread(self):
        # makes sure that post counts are updated when a thread is moved
        self.fail()

class WatchTester(TestCase):
    fixtures = ('vcboard',)

    def testWatchTopic(self):
        # ensures that users will be notified when a topic changes
        self.fail()

    def testWatchForum(self):
        # ensures that users will be notified when a forum changes
        self.fail()

class SignalTester(TestCase):
    fixtures = ('vcboard',)
    
    def testThreadCreated(self):
        # ensures that the signal is fired when a new thread is created
        self.fail()

    def testThreadUpdated(self):
        # ensures that the signal is fired when a thread is updated
        self.fail()

    def testThreadMoved(self):
        # ensures that the signal is fired when a thread is moved
        self.fail()

    def testThreadDeleted(self):
        # ensures that the signal is fired when a thread is deleted
        self.fail()

    def testThreadSticky(self):
        # ensures that the signal is fired when a thread is made sticky
        self.fail()

    def testThreadUnsticky(self):
        # ensures that the signal is fired when a thread is made unsticky
        self.fail()

    def testThreadClosed(self):
        # ensures that the signal is fired when a thread is closed
        self.fail()

    def testThreadReopened(self):
        # ensures that the signal is fired when a thread is reopened
        self.fail()

    def testForumPruned(self):
        # ensures that the signal is fired when a forum is pruned
        self.fail()

    def testUserRegistered(self):
        # ensures that the signal is fired when a new user registers
        self.fail()
