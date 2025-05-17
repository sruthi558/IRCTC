import React from "react";
import ThreateCard from "./ThreateCard";
import styles from "./touts-details.module.scss";

const ThreatCards = ({ data }) => {
  const shouldDisplayReadMore = (item) =>
  item?.Contact?.length > 1 ||
  item?.Email?.length > 1 ||
  item?.Youtube?.length > 1 ||
  item?.Telegram?.length > 1 ||
  item?.Website?.length > 1 ||
  item?.Whatsapp?.length > 1;

const sortedData = data?.sort((a, b) => {
  const shouldDisplayReadMoreA = shouldDisplayReadMore(a);
  const shouldDisplayReadMoreB = shouldDisplayReadMore(b);

  return shouldDisplayReadMoreB - shouldDisplayReadMoreA;
});
  return (
    <>
      <div className={styles.threatCards}>
      <div className={styles.TextStyling}>
          <p className={styles.TextStylings}>
            Pinaca has discovered actionable details about these touts, such as
            their phone numbers, email addresses, physical addresses, and the
            source from which they sell Tatkal Booking software. These
            individuals are using social media to connect with potential
            customers and offer their services.
          </p>
        </div>
        {sortedData?.map((threat, index) => (
          <ThreateCard
           key={index}
           data={threat} 
           completeData={threat}
           displayReadMoreButton={shouldDisplayReadMore(threat)}/>
        ))}
        
      </div>
     
    </>
  );
};
export default ThreatCards;
