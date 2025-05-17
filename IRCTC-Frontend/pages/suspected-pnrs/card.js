import React from "react";
import { Panel, Row, Col } from "rsuite";

const Card = (card) => {
  if (card?.card?.COMMENT) {
    return (
      <Panel bordered shaded header={card.card.EMAIL}>
        <Row>
          <Col xs={12}>{card.card.COMMENT}</Col>
          <Col xsPush={6}>
            {card.card.DATE != undefined
              ? new Date(card?.card?.DATE?.$date).toDateString()
              : null}
          </Col>
        </Row>
      </Panel>
    );
  } else {
    return (
      <Panel bordered shaded >
        <Row>
          <Col>
            <h4>Write a Feedback!</h4>
          </Col>
        </Row>
      </Panel>
    );
  }
};

export default Card;
