from __future__ import absolute_import

import six
from datetime import timedelta

from django.core.urlresolvers import reverse

from sentry.utils.samples import load_data
from sentry.testutils import APITestCase, SnubaTestCase
from sentry.testutils.helpers import parse_link_header
from sentry.testutils.helpers.datetime import before_now, iso_format


class OrganizationEventsTrendsEndpointTest(APITestCase, SnubaTestCase):
    def setUp(self):
        super(OrganizationEventsTrendsEndpointTest, self).setUp()
        self.login_as(user=self.user)

        self.day_ago = before_now(days=1).replace(hour=10, minute=0, second=0, microsecond=0)

        self.project = self.create_project()
        self.prototype = load_data("transaction")
        data = self.prototype.copy()
        data["start_timestamp"] = iso_format(self.day_ago + timedelta(minutes=30))
        data["user"] = {"email": "foo@example.com"}
        data["timestamp"] = iso_format(self.day_ago + timedelta(minutes=30, seconds=2))
        self.store_event(data, project_id=self.project.id)

        second = [0, 2, 10]
        for i in range(3):
            data = self.prototype.copy()
            data["start_timestamp"] = iso_format(self.day_ago + timedelta(hours=1, minutes=30))
            data["timestamp"] = iso_format(
                self.day_ago + timedelta(hours=1, minutes=30, seconds=second[i])
            )
            data["user"] = {"email": "foo{}@example.com".format(i)}
            self.store_event(data, project_id=self.project.id)

    def test_simple(self):
        with self.feature("organizations:trends"):
            url = reverse(
                "sentry-api-0-organization-events-trends",
                kwargs={"organization_slug": self.project.organization.slug},
            )
            response = self.client.get(
                url,
                format="json",
                data={
                    "end": iso_format(self.day_ago + timedelta(hours=2)),
                    "start": iso_format(self.day_ago),
                    "field": ["project", "transaction"],
                    "query": "event.type:transaction",
                },
            )

        assert response.status_code == 200, response.content

        events = response.data["events"]
        result_stats = response.data["stats"]

        assert len(events["data"]) == 1
        # Shouldn't do an exact match here because we aren't using the stable correlation function
        assert events["data"][0].pop("absolute_correlation") > 0.2
        assert events["data"][0] == {
            "count_range_1": 1,
            "count_range_2": 3,
            "transaction": self.prototype["transaction"],
            "project": self.project.slug,
            "percentile_range_1": 2000,
            "percentile_range_2": 2000,
            "percentage_count_range_2_count_range_1": 3.0,
            "minus_percentile_range_2_percentile_range_1": 0.0,
            "percentage_percentile_range_2_percentile_range_1": 1.0,
        }

        stats = result_stats["{},{}".format(self.project.slug, self.prototype["transaction"])]
        assert [attrs for time, attrs in stats["data"]] == [
            [{"count": 2000}],
            [{"count": 2000}],
        ]

    def test_avg_trend_function(self):
        with self.feature("organizations:trends"):
            url = reverse(
                "sentry-api-0-organization-events-trends",
                kwargs={"organization_slug": self.project.organization.slug},
            )
            response = self.client.get(
                url,
                format="json",
                data={
                    "end": iso_format(self.day_ago + timedelta(hours=2)),
                    "start": iso_format(self.day_ago),
                    "field": ["project", "transaction"],
                    "query": "event.type:transaction",
                    "trendFunction": "avg(transaction.duration)",
                    "project": [self.project.id],
                },
            )
        assert response.status_code == 200, response.content

        events = response.data["events"]
        result_stats = response.data["stats"]

        assert len(events["data"]) == 1
        # Shouldn't do an exact match here because we aren't using the stable correlation function
        assert events["data"][0].pop("absolute_correlation") > 0.2
        assert events["data"][0] == {
            "count_range_2": 3,
            "count_range_1": 1,
            "transaction": self.prototype["transaction"],
            "project": self.project.slug,
            "avg_range_1": 2000,
            "avg_range_2": 4000,
            "percentage_count_range_2_count_range_1": 3.0,
            "minus_avg_range_2_avg_range_1": 2000.0,
            "percentage_avg_range_2_avg_range_1": 2.0,
        }

        stats = result_stats["{},{}".format(self.project.slug, self.prototype["transaction"])]
        assert [attrs for time, attrs in stats["data"]] == [
            [{"count": 2000}],
            [{"count": 4000}],
        ]

    def test_misery_trend_function(self):
        with self.feature("organizations:trends"):
            url = reverse(
                "sentry-api-0-organization-events-trends",
                kwargs={"organization_slug": self.project.organization.slug},
            )
            response = self.client.get(
                url,
                format="json",
                data={
                    "end": iso_format(self.day_ago + timedelta(hours=2)),
                    "start": iso_format(self.day_ago),
                    "field": ["project", "transaction"],
                    "query": "event.type:transaction",
                    "trendFunction": "user_misery(300)",
                    "project": [self.project.id],
                },
            )
        assert response.status_code == 200, response.content

        events = response.data["events"]
        result_stats = response.data["stats"]

        assert len(events["data"]) == 1
        # Shouldn't do an exact match here because we aren't using the stable correlation function
        assert events["data"][0].pop("absolute_correlation") > 0.2
        assert events["data"][0] == {
            "count_range_2": 3,
            "count_range_1": 1,
            "transaction": self.prototype["transaction"],
            "project": self.project.slug,
            "user_misery_range_1": 1,
            "user_misery_range_2": 2,
            "percentage_count_range_2_count_range_1": 3.0,
            "minus_user_misery_range_2_user_misery_range_1": 1.0,
            "percentage_user_misery_range_2_user_misery_range_1": 2.0,
        }

        stats = result_stats["{},{}".format(self.project.slug, self.prototype["transaction"])]
        assert [attrs for time, attrs in stats["data"]] == [
            [{"count": 1}],
            [{"count": 2}],
        ]

    def test_invalid_trend_function(self):
        with self.feature("organizations:trends"):
            url = reverse(
                "sentry-api-0-organization-events-trends",
                kwargs={"organization_slug": self.project.organization.slug},
            )
            response = self.client.get(
                url,
                format="json",
                data={
                    "end": iso_format(self.day_ago + timedelta(hours=2)),
                    "start": iso_format(self.day_ago),
                    "field": ["project", "transaction"],
                    "query": "event.type:transaction",
                    "trendFunction": "apdex(450)",
                    "project": [self.project.id],
                },
            )
            assert response.status_code == 400

    def test_divide_by_zero(self):
        with self.feature("organizations:trends"):
            url = reverse(
                "sentry-api-0-organization-events-trends",
                kwargs={"organization_slug": self.project.organization.slug},
            )
            response = self.client.get(
                url,
                format="json",
                data={
                    # Set the timeframe to where the second range has no transactions so all the counts/percentile are 0
                    "end": iso_format(self.day_ago + timedelta(hours=2)),
                    "start": iso_format(self.day_ago - timedelta(hours=2)),
                    "field": ["project", "transaction"],
                    "query": "event.type:transaction",
                    "project": [self.project.id],
                },
            )
        assert response.status_code == 200, response.content

        events = response.data["events"]
        result_stats = response.data["stats"]

        assert len(events["data"]) == 1
        # Shouldn't do an exact match here because we aren't using the stable correlation function
        assert events["data"][0].pop("absolute_correlation") > 0.2
        assert events["data"][0] == {
            "count_range_2": 4,
            "count_range_1": 0,
            "transaction": self.prototype["transaction"],
            "project": self.project.slug,
            "percentile_range_1": 0,
            "percentile_range_2": 2000.0,
            "percentage_count_range_2_count_range_1": None,
            "minus_percentile_range_2_percentile_range_1": 0,
            "percentage_percentile_range_2_percentile_range_1": None,
        }

        stats = result_stats["{},{}".format(self.project.slug, self.prototype["transaction"])]
        assert [attrs for time, attrs in stats["data"]] == [
            [{"count": 0}],
            [{"count": 0}],
            [{"count": 2000}],
            [{"count": 2000}],
        ]


class OrganizationEventsTrendsPagingTest(APITestCase, SnubaTestCase):
    def setUp(self):
        super(OrganizationEventsTrendsPagingTest, self).setUp()
        self.login_as(user=self.user)

        self.day_ago = before_now(days=1).replace(hour=10, minute=0, second=0, microsecond=0)

        self.project = self.create_project()
        self.prototype = load_data("transaction")

        # Make 10 transactions for paging
        for i in range(10):
            for j in range(2):
                data = self.prototype.copy()
                data["user"] = {"email": "foo@example.com"}
                data["start_timestamp"] = iso_format(self.day_ago + timedelta(minutes=30))
                data["timestamp"] = iso_format(
                    self.day_ago + timedelta(hours=j, minutes=30, seconds=2)
                )
                if i < 5:
                    data["transaction"] = "transaction_1{}".format(i)
                else:
                    data["transaction"] = "transaction_2{}".format(i)
                self.store_event(data, project_id=self.project.id)

    def _parse_links(self, header):
        # links come in {url: {...attrs}}, but we need {rel: {...attrs}}
        links = {}
        for url, attrs in six.iteritems(parse_link_header(header)):
            links[attrs["rel"]] = attrs
            attrs["href"] = url
        return links

    def test_pagination(self):
        with self.feature("organizations:trends"):
            url = reverse(
                "sentry-api-0-organization-events-trends",
                kwargs={"organization_slug": self.project.organization.slug},
            )
            response = self.client.get(
                url,
                format="json",
                data={
                    # Set the timeframe to where the second range has no transactions so all the counts/percentile are 0
                    "end": iso_format(self.day_ago + timedelta(hours=2)),
                    "start": iso_format(self.day_ago - timedelta(hours=2)),
                    "field": ["project", "transaction"],
                    "query": "event.type:transaction",
                    "project": [self.project.id],
                },
            )
            assert response.status_code == 200, response.content

            links = self._parse_links(response["Link"])
            assert links["previous"]["results"] == "false"
            assert links["next"]["results"] == "true"
            assert len(response.data["events"]["data"]) == 5

            response = self.client.get(links["next"]["href"], format="json")
            assert response.status_code == 200, response.content

            links = self._parse_links(response["Link"])
            assert links["previous"]["results"] == "true"
            assert links["next"]["results"] == "false"
            assert len(response.data["events"]["data"]) == 5

    def test_pagination_with_query(self):
        with self.feature("organizations:trends"):
            url = reverse(
                "sentry-api-0-organization-events-trends",
                kwargs={"organization_slug": self.project.organization.slug},
            )
            response = self.client.get(
                url,
                format="json",
                data={
                    # Set the timeframe to where the second range has no transactions so all the counts/percentile are 0
                    "end": iso_format(self.day_ago + timedelta(hours=2)),
                    "start": iso_format(self.day_ago - timedelta(hours=2)),
                    "field": ["project", "transaction"],
                    "query": "event.type:transaction transaction:transaction_1*",
                    "project": [self.project.id],
                },
            )
            assert response.status_code == 200, response.content

            links = self._parse_links(response["Link"])
            assert links["previous"]["results"] == "false"
            assert links["next"]["results"] == "false"
            assert len(response.data["events"]["data"]) == 5
