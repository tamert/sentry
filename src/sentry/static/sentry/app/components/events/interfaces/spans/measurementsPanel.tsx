import React from 'react';
import styled from '@emotion/styled';

import {SentryTransactionEvent} from 'app/types';
import {defined} from 'app/utils';
import {WEB_VITAL_DETAILS} from 'app/views/performance/realUserMonitoring/constants';

import {
  getMeasurements,
  toPercent,
  getMeasurementBounds,
  SpanBoundsType,
  SpanGeneratedBoundsType,
} from './utils';

const MEASUREMENT_ACRONYMS = Object.fromEntries(
  Object.values(WEB_VITAL_DETAILS).map(value => {
    return [value.slug, value.acronym];
  })
);

type Props = {
  event: SentryTransactionEvent;
  generateBounds: (bounds: SpanBoundsType) => SpanGeneratedBoundsType;
};
class MeasurementsPanel extends React.PureComponent<Props> {
  render() {
    const {event, generateBounds} = this.props;

    const measurements = getMeasurements(event);

    console.log('measurements', measurements);

    return (
      <Container>
        {measurements.map(measurement => {
          const bounds = getMeasurementBounds(measurement.timestamp, generateBounds);

          const shouldDisplay = defined(bounds.left) && defined(bounds.width);

          if (!shouldDisplay) {
            return null;
          }

          const slug = measurement.name.slice('mark.'.length);

          return (
            <MeasurementMarker
              key={measurement.name}
              style={{
                left: `${toPercent(bounds.left || 0)}`,
              }}
            >
              <Label>{MEASUREMENT_ACRONYMS[slug]}</Label>
            </MeasurementMarker>
          );
        })}
      </Container>
    );
  }
}

const Container = styled('div')`
  position: relative;
  flex-grow: 1;
  overflow: hidden;

  height: 20px;
`;

const MeasurementMarker = styled('div')`
  position: absolute;
  top: 0;
  height: 100%;
  user-select: none;
`;

const Label = styled('div')`
  transform: translateX(-50%);
  font-size: ${p => p.theme.fontSizeExtraSmall};
`;

export default MeasurementsPanel;
