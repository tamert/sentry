import React from 'react';
import styled from '@emotion/styled';
import {Link} from 'react-router';
import * as queryString from 'query-string';
import {Query, Location} from 'history';

import {EventTag} from 'app/types';
import AnnotatedText from 'app/components/events/meta/annotatedText';
import {isUrl} from 'app/utils';
import Pill from 'app/components/pill';
import VersionHoverCard from 'app/components/versionHoverCard';
import TraceHoverCard from 'app/utils/discover/traceHoverCard';
import {IconOpen, IconInfo} from 'app/icons';
import ExternalLink from 'app/components/links/externalLink';
import {getMeta} from 'app/components/events/meta/metaProxy';

import EventTagsPillValue from './eventTagsPillValue';

type Props = {
  tag: EventTag;
  streamPath: string;
  releasesPath: string;
  query: Query;
  location: Location;
  orgId: string;
  projectId: string;
  hasQueryFeature: boolean;
};

const EventTagsPill = ({
  tag,
  query,
  orgId,
  projectId,
  streamPath,
  releasesPath,
  location,
  hasQueryFeature,
}: Props) => {
  const locationSearch = `?${queryString.stringify(query)}`;
  const isRelease = tag.key === 'release';
  const isTrace = tag.key === 'trace';
  const key = tag.key;

  return (
    <Pill
      name={!tag.key ? <AnnotatedText value={key} meta={getMeta(tag, 'key')} /> : key}
      value={tag.value}
      type={!tag.key ? 'error' : undefined}
    >
      <EventTagsPillValue
        key={key}
        value={tag.value}
        meta={getMeta(tag, 'value')}
        streamPath={streamPath}
        locationSearch={locationSearch}
        isRelease={isRelease}
      />
      {isUrl(tag.value) && (
        <ExternalLink href={tag.value} className="external-icon">
          <StyledIconOpen size="xs" />
        </ExternalLink>
      )}
      {isRelease && (
        <div className="pill-icon">
          <VersionHoverCard
            orgSlug={orgId}
            projectSlug={projectId}
            releaseVersion={tag.value}
          >
            <Link
              to={{
                pathname: `${releasesPath}${tag.value}/`,
                search: locationSearch,
              }}
            >
              <StyledIconInfo size="xs" />
            </Link>
          </VersionHoverCard>
        </div>
      )}
      {isTrace && hasQueryFeature && (
        <TraceHoverCard
          containerClassName="pill-icon"
          traceId={tag.value}
          orgId={orgId}
          location={location}
        >
          {({to}) => {
            return (
              <Link to={to}>
                <StyledIconOpen size="xs" />
              </Link>
            );
          }}
        </TraceHoverCard>
      )}
    </Pill>
  );
};

const StyledIconInfo = styled(IconInfo)`
  position: relative;
  top: 1px;
`;

const StyledIconOpen = styled(IconOpen)`
  position: relative;
  top: 1px;
`;

export default EventTagsPill;
