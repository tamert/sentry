import React from 'react';
import styled from '@emotion/styled';

import {SentryTransactionEvent} from 'app/types';
import {defined} from 'app/utils';

import {
  getMeasurements,
  toPercent,
  getMeasurementBounds,
  SpanBoundsType,
  SpanGeneratedBoundsType,
} from './utils';

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

          return (
            <MeasurementMarker
              key={measurement.name}
              style={{
                left: `calc(${toPercent(bounds.left || 0)} + 1.5px)`,
              }}
            />
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
  width: 1px;
  user-select: none;

  background-color: ${p => p.theme.gray800};
`;

export default MeasurementsPanel;
